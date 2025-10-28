from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import Dict, Any
import logging

# Import activities
with workflow.unsafe.imports_passed_through():
    from activities import twilio_activities, database_activities, circle_activities

logger = logging.getLogger(__name__)


@workflow.defn
class RegistrationWorkflow:
    """
    User registration workflow
    
    Steps:
    1. Create user in database
    2. Send verification code
    3. Wait for code verification (via signal)
    4. Generate PIN setup token
    5. Send PIN setup link
    6. Wait for PIN setup (via signal)
    7. Create Circle wallet
    8. Complete registration
    9. Send welcome message
    """
    
    def __init__(self):
        self.phone_number: str = ""
        self.verification_code: str = ""
        self.code_verified: bool = False
        self.pin_setup_token: str = ""
        self.pin_set: bool = False
        self.wallet_created: bool = False
    
    @workflow.run
    async def run(self, phone_number: str) -> Dict[str, Any]:
        """
        Execute registration workflow
        
        Args:
            phone_number: User's WhatsApp number
        
        Returns:
            Registration result with user data
        """
        self.phone_number = phone_number
        
        workflow.logger.info(f"Starting registration for {phone_number}")
        
        # Step 1: Create user and get verification code
        user_data = await workflow.execute_activity(
            database_activities.create_user,
            phone_number,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.verification_code = user_data["verification_code"]
        
        # Step 2: Send verification code
        await workflow.execute_activity(
            twilio_activities.send_verification_code,
            args=[phone_number, self.verification_code],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 3: Wait for verification (signal or timeout after 10 minutes)
        workflow.logger.info(f"Waiting for verification code from {phone_number}")
        
        await workflow.wait_condition(
            lambda: self.code_verified,
            timeout=timedelta(minutes=10)
        )
        
        if not self.code_verified:
            workflow.logger.warning(f"Verification timeout for {phone_number}")
            await workflow.execute_activity(
                twilio_activities.send_error_message,
                args=[phone_number, "general"],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return {"success": False, "error": "verification_timeout"}
        
        # Step 4: Generate PIN setup token (using workflow.uuid4 for determinism)
        self.pin_setup_token = str(workflow.uuid4())
        
        # Step 5: Send PIN setup link
        await workflow.execute_activity(
            twilio_activities.send_pin_setup_link,
            args=[phone_number, self.pin_setup_token],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 6: Wait for PIN setup (signal or timeout after 15 minutes)
        workflow.logger.info(f"Waiting for PIN setup from {phone_number}")
        
        await workflow.wait_condition(
            lambda: self.pin_set,
            timeout=timedelta(minutes=15)
        )
        
        if not self.pin_set:
            workflow.logger.warning(f"PIN setup timeout for {phone_number}")
            await workflow.execute_activity(
                twilio_activities.send_error_message,
                args=[phone_number, "general"],
                start_to_close_timeout=timedelta(seconds=30)
            )
            return {"success": False, "error": "pin_setup_timeout"}
        
        # Step 7: Create Circle wallet
        wallet_data = await workflow.execute_activity(
            circle_activities.create_circle_wallet,
            phone_number,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 8: Update user with wallet info
        await workflow.execute_activity(
            database_activities.update_user_wallet,
            args=[
                phone_number,
                wallet_data["wallet_id"],
                wallet_data["wallet_address"]
            ],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        self.wallet_created = True
        
        # Step 9: Send welcome message
        await workflow.execute_activity(
            twilio_activities.send_welcome_message,
            args=[phone_number, None],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        workflow.logger.info(f"Registration completed for {phone_number}")
        
        return {
            "success": True,
            "phone_number": phone_number,
            "wallet_id": wallet_data["wallet_id"],
            "wallet_address": wallet_data["wallet_address"]
        }
    
    @workflow.signal
    async def verify_code(self, code: str):
        """Signal to verify code"""
        workflow.logger.info(f"Received verification code: {code}")
        
        if code == self.verification_code:
            # Verify in database
            verified = await workflow.execute_activity(
                database_activities.verify_user_code,
                args=[self.phone_number, code],
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            if verified:
                self.code_verified = True
                workflow.logger.info(f"Code verified for {self.phone_number}")
    
    @workflow.signal
    async def set_pin(self, args: dict):
        """Signal to set PIN"""
        workflow.logger.info(f"Received PIN setup request")
        
        pin_hash = args.get("pin_hash")
        token = args.get("token")
        
        # Verify token matches
        if token != self.pin_setup_token:
            workflow.logger.warning("Invalid PIN setup token")
            return
        
        # Save PIN hash to database
        success = await workflow.execute_activity(
            database_activities.update_user_pin,
            args=[self.phone_number, pin_hash],
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        if success:
            self.pin_set = True
            workflow.logger.info(f"PIN set for {self.phone_number}")
    
    @workflow.query
    def get_status(self) -> Dict[str, bool]:
        """Query current registration status"""
        return {
            "code_verified": self.code_verified,
            "pin_set": self.pin_set,
            "wallet_created": self.wallet_created
        }