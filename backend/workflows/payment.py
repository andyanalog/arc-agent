from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta, datetime
from typing import Dict, Any
import logging

with workflow.unsafe.imports_passed_through():
    from activities import twilio_activities, database_activities, circle_activities

logger = logging.getLogger(__name__)


@workflow.defn
class PaymentWorkflow:
    """
    Payment execution workflow
    
    Steps:
    1. Parse payment request (amount, recipient)
    2. Validate user has sufficient balance
    3. Request confirmation from user
    4. Wait for confirmation (via signal)
    5. Execute transfer via Circle
    6. Update transaction status
    7. Send receipt to user
    """
    
    def __init__(self):
        self.phone_number: str = ""
        self.amount: float = 0.0
        self.recipient: str = ""
        self.recipient_address: str = ""
        self.confirmed: bool = False
        self.cancelled: bool = False
        self.transaction_id: str = ""
    
    @workflow.run
    async def run(
        self,
        phone_number: str,
        amount: float,
        recipient: str
    ) -> Dict[str, Any]:
        """
        Execute payment workflow
        
        Args:
            phone_number: Sender's phone number
            amount: Amount in USDC
            recipient: Recipient identifier (name/phone/address)
        
        Returns:
            Payment result
        """
        self.phone_number = phone_number
        self.amount = amount
        self.recipient = recipient
        
        workflow.logger.info(f"Starting payment: {phone_number} -> {recipient} ${amount}")
        
        # Step 1: Get user data
        user_data = await workflow.execute_activity(
            database_activities.get_user,
            phone_number,
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        if not user_data or not user_data["registration_completed"]:
            workflow.logger.error(f"User not registered: {phone_number}")
            await workflow.execute_activity(
                twilio_activities.send_error_message,
                args=[phone_number, "general"],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return {"success": False, "error": "user_not_registered"}
        
        wallet_id = user_data["circle_wallet_id"]
        
        # Step 2: Check balance
        balance = await workflow.execute_activity(
            circle_activities.get_wallet_balance,
            wallet_id,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if balance < amount:
            workflow.logger.warning(f"Insufficient funds for {phone_number}: ${balance} < ${amount}")
            await workflow.execute_activity(
                twilio_activities.send_error_message,
                args=[phone_number, "insufficient_funds"],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return {"success": False, "error": "insufficient_funds"}
        
        # Step 3: Resolve recipient address
        self.recipient_address = await workflow.execute_activity(
            circle_activities.resolve_recipient_address,
            recipient,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 4: Create transaction record
        self.transaction_id = await workflow.execute_activity(
            database_activities.create_transaction,
            args=[phone_number, "send", amount, recipient, self.recipient_address],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Step 5: Request confirmation
        await workflow.execute_activity(
            twilio_activities.send_confirmation_request,
            args=[phone_number, "send", amount, recipient],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 6: Wait for confirmation (2 minutes timeout)
        workflow.logger.info(f"Waiting for payment confirmation from {phone_number}")
        
        await workflow.wait_condition(
            lambda: self.confirmed or self.cancelled,
            timeout=timedelta(minutes=2)
        )
        
        if self.cancelled:
            workflow.logger.info(f"Payment cancelled by user: {phone_number}")
            await workflow.execute_activity(
                database_activities.update_transaction_status,
                args=[self.transaction_id, "cancelled", None],
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            await workflow.execute_activity(
                twilio_activities.send_custom_message,
                args=[phone_number, "❌ Payment cancelled."],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return {"success": False, "error": "cancelled_by_user"}
        
        if not self.confirmed:
            workflow.logger.warning(f"Confirmation timeout for {phone_number}")
            await workflow.execute_activity(
                database_activities.update_transaction_status,
                args=[self.transaction_id, "timeout", None],
                start_to_close_timeout=timedelta(seconds=10)
            )
            return {"success": False, "error": "confirmation_timeout"}
        
        # Step 7: Execute transfer
        workflow.logger.info(f"Executing transfer for {phone_number}")
        
        transfer_result = await workflow.execute_activity(
            circle_activities.initiate_transfer,
            args=[wallet_id, self.recipient_address, amount],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 8: Check transfer status
        transfer_status = await workflow.execute_activity(
            circle_activities.check_transfer_status,
            transfer_result["transfer_id"],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=5)
        )
        
        tx_hash = transfer_status["tx_hash"]
        
        # Step 9: Update transaction
        await workflow.execute_activity(
            database_activities.update_transaction_status,
            args=[self.transaction_id, "confirmed", tx_hash],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Step 10: Send receipt
        timestamp = workflow.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        await workflow.execute_activity(
            twilio_activities.send_transaction_receipt,
            args=[phone_number, amount, recipient, tx_hash, timestamp],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        workflow.logger.info(f"Payment completed: {tx_hash}")
        
        return {
            "success": True,
            "transaction_id": self.transaction_id,
            "tx_hash": tx_hash,
            "amount": amount,
            "recipient": recipient
        }
    
    @workflow.signal
    async def confirm_payment(self):
        """Signal to confirm payment"""
        workflow.logger.info(f"Payment confirmed by {self.phone_number}")
        self.confirmed = True
    
    @workflow.signal
    async def cancel_payment(self):
        """Signal to cancel payment"""
        workflow.logger.info(f"Payment cancelled by {self.phone_number}")
        self.cancelled = True
    
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current payment status"""
        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "recipient": self.recipient,
            "confirmed": self.confirmed,
            "cancelled": self.cancelled
        }