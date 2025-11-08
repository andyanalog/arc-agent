import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from config import settings
from workflows.registration import RegistrationWorkflow
from workflows.payment import PaymentWorkflow
from activities import twilio_activities, database_activities, circle_activities, pin_activities

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Start Temporal worker"""
    
    logger.info("Connecting to Temporal server...")
    
    # Connect to Temporal with retries
    max_retries = 10
    retry_delay = 5
    client = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Connection attempt {attempt + 1}/{max_retries}...")
            client = await Client.connect(settings.TEMPORAL_HOST)
            logger.info(f"Connected to Temporal at {settings.TEMPORAL_HOST}")
            break
        except Exception as e:
            logger.warning(f"Failed to connect to Temporal: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Could not connect to Temporal after all retries")
                raise
    
    if not client:
        raise RuntimeError("Failed to connect to Temporal")
    
    # Create worker
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[
            RegistrationWorkflow,
            PaymentWorkflow,
        ],
        activities=[
            # Twilio activities
            twilio_activities.send_verification_code,
            twilio_activities.send_welcome_message,
            twilio_activities.send_pin_setup_link,
            twilio_activities.send_confirmation_request,
            twilio_activities.send_transaction_receipt,
            twilio_activities.send_error_message,
            twilio_activities.send_custom_message,
            
            # Database activities
            database_activities.create_user,
            database_activities.auto_verify_user,
            database_activities.verify_user_code,
            database_activities.get_user,
            database_activities.update_user_pin,
            database_activities.update_user_wallet,
            database_activities.log_message,
            database_activities.create_transaction,
            database_activities.update_transaction_status,
            
            # PIN activities
            pin_activities.verify_user_pin,
            
            # Circle activities
            circle_activities.create_circle_wallet,
            circle_activities.get_wallet_balance,
            circle_activities.initiate_transfer,
            circle_activities.check_transfer_status,
            circle_activities.resolve_recipient_address,
        ],
    )
    
    logger.info(f"Worker started on task queue: {settings.TEMPORAL_TASK_QUEUE}")
    logger.info("Waiting for workflows and activities...")
    
    # Run worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())