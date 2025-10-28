from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import Response
from temporalio.client import Client
from sqlalchemy.orm import Session
import logging
import asyncio
from typing import Optional

from config import settings
from models.database import init_db, get_db
from services.message_parser import MessageParser, Intent
from workflows.registration import RegistrationWorkflow
from workflows.payment import PaymentWorkflow

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ArcAgent API",
    description="WhatsApp-based USDC payment assistant",
    version="0.1.0"
)

# Store Temporal client globally
temporal_client: Optional[Client] = None


@app.on_event("startup")
async def startup_event():
    """Initialize database and Temporal client on startup"""
    global temporal_client
    
    logger.info("Starting ArcAgent API...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Connect to Temporal with retries
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to Temporal (attempt {attempt + 1}/{max_retries})...")
            temporal_client = await Client.connect(settings.TEMPORAL_HOST)
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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ArcAgent API...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ArcAgent API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "temporal_connected": temporal_client is not None
    }


@app.post("/webhooks/twilio/incoming")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle incoming WhatsApp messages from Twilio
    
    This endpoint receives messages and routes them to appropriate workflows
    """
    try:
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = From.replace('whatsapp:', '')
        message_body = Body.strip()
        
        logger.info(f"Received message from {phone_number}: {message_body}")
        
        # Parse message intent
        parsed = MessageParser.parse(message_body)
        intent = parsed['intent']
        params = parsed['params']
        
        logger.info(f"Parsed intent: {intent}, params: {params}")
        
        # Log message to database
        from activities.database_activities import log_message
        await log_message(
            phone_number=phone_number,
            direction="inbound",
            message_body=message_body,
            message_sid=MessageSid,
            intent=intent
        )
        
        # Route based on intent
        if intent == Intent.REGISTRATION:
            await handle_registration(phone_number)
        
        elif intent == Intent.SEND_MONEY:
            await handle_send_money(phone_number, params)
        
        elif intent == Intent.CHECK_BALANCE:
            await handle_check_balance(phone_number)
        
        elif intent == Intent.CONFIRM:
            await handle_confirmation(phone_number)
        
        elif intent == Intent.CANCEL:
            await handle_cancellation(phone_number)
        
        elif intent == Intent.HELP:
            await handle_help(phone_number)
        
        else:
            await handle_unknown_intent(phone_number, message_body)
        
        # Return TwiML response (empty for now)
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_registration(phone_number: str):
    """Start registration workflow"""
    try:
        workflow_id = f"registration-{phone_number}"
        
        # Check if workflow already exists
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
            status = await handle.query(RegistrationWorkflow.get_status)
            
            logger.info(f"Registration workflow already exists for {phone_number}: {status}")
            
            # Send status update
            from services.twilio_service import twilio_service
            if status['wallet_created']:
                twilio_service.send_message(phone_number, "✅ You're already registered! Type 'help' to see what you can do.")
            elif status['pin_set']:
                twilio_service.send_message(phone_number, "⏳ Setting up your wallet... This will take a moment.")
            elif status['code_verified']:
                twilio_service.send_message(phone_number, "⏳ Please complete your PIN setup using the link sent earlier.")
            else:
                twilio_service.send_message(phone_number, "⏳ Please verify your code. Check your messages!")
            
            return
            
        except:
            # Workflow doesn't exist, create new one
            pass
        
        # Start new registration workflow
        await temporal_client.start_workflow(
            RegistrationWorkflow.run,
            phone_number,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE
        )
        
        logger.info(f"Started registration workflow for {phone_number}")
    
    except Exception as e:
        logger.error(f"Error starting registration: {str(e)}", exc_info=True)
        from services.twilio_service import twilio_service
        twilio_service.send_error_message(phone_number)


async def handle_send_money(phone_number: str, params: dict):
    """Start payment workflow"""
    try:
        amount = params.get('amount')
        recipient = params.get('recipient')
        
        if not amount or not recipient:
            from services.twilio_service import twilio_service
            twilio_service.send_error_message(phone_number, "invalid_amount")
            return
        
        workflow_id = f"payment-{phone_number}-{int(amount * 100)}-{hash(recipient)}"
        
        # Start payment workflow
        await temporal_client.start_workflow(
            PaymentWorkflow.run,
            args=[phone_number, amount, recipient],
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE
        )
        
        logger.info(f"Started payment workflow for {phone_number}: ${amount} to {recipient}")
    
    except Exception as e:
        logger.error(f"Error starting payment: {str(e)}", exc_info=True)
        from services.twilio_service import twilio_service
        twilio_service.send_error_message(phone_number)


async def handle_check_balance(phone_number: str):
    """Handle balance check request"""
    try:
        from activities.database_activities import get_user
        from activities.circle_activities import get_wallet_balance
        
        # Get user
        user_data = await get_user(phone_number)
        
        if not user_data or not user_data['registration_completed']:
            from services.twilio_service import twilio_service
            twilio_service.send_message(
                phone_number,
                "❌ Please register first! Send 'Hi' to get started."
            )
            return
        
        # Get balance
        balance = await get_wallet_balance(user_data['circle_wallet_id'])
        
        # Send balance
        from services.twilio_service import twilio_service
        message = f"💰 Your Balance: ${balance:.2f} USDC\n\nWallet: {user_data['circle_wallet_address'][:10]}...{user_data['circle_wallet_address'][-8:]}"
        twilio_service.send_message(phone_number, message)
        
        logger.info(f"Sent balance to {phone_number}: ${balance}")
    
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}", exc_info=True)
        from services.twilio_service import twilio_service
        twilio_service.send_error_message(phone_number)


async def handle_confirmation(phone_number: str):
    """Handle confirmation from user"""
    try:
        # List all running workflows and filter manually
        from temporalio.client import WorkflowExecutionStatus
        
        async for workflow in temporal_client.list_workflows('ExecutionStatus = "Running"'):
            # Check if workflow ID matches payment pattern for this user
            if workflow.id.startswith(f"payment-{phone_number}"):
                handle = temporal_client.get_workflow_handle(workflow.id)
                
                # Send confirmation signal
                await handle.signal(PaymentWorkflow.confirm_payment)
                logger.info(f"Sent confirmation signal to workflow {workflow.id}")
                return
        
        # No active workflow found
        from services.twilio_service import twilio_service
        twilio_service.send_message(phone_number, "❌ No pending action to confirm.")
    
    except Exception as e:
        logger.error(f"Error handling confirmation: {str(e)}", exc_info=True)


async def handle_cancellation(phone_number: str):
    """Handle cancellation from user"""
    try:
        # List all running workflows and filter manually
        from temporalio.client import WorkflowExecutionStatus
        
        async for workflow in temporal_client.list_workflows('ExecutionStatus = "Running"'):
            # Check if workflow ID matches payment pattern for this user
            if workflow.id.startswith(f"payment-{phone_number}"):
                handle = temporal_client.get_workflow_handle(workflow.id)
                
                # Send cancellation signal
                await handle.signal(PaymentWorkflow.cancel_payment)
                logger.info(f"Sent cancellation signal to workflow {workflow.id}")
                return
        
        # No active workflow found
        from services.twilio_service import twilio_service
        twilio_service.send_message(phone_number, "✅ No pending action to cancel.")
    
    except Exception as e:
        logger.error(f"Error handling cancellation: {str(e)}", exc_info=True)


async def handle_help(phone_number: str):
    """Send help message"""
    try:
        from services.twilio_service import twilio_service
        
        help_text = """🤖 ArcAgent Help

💸 Send money:
"Send $20 to John"
"Pay Alice $50"

💰 Check balance:
"Balance"
"How much do I have?"

📊 Transaction history:
"Show transactions"
"History"

⚙️ Settings:
"Settings"

🆘 Need more help?
Contact support@arcagent.example.com
        """
        
        twilio_service.send_message(phone_number, help_text)
        logger.info(f"Sent help message to {phone_number}")
    
    except Exception as e:
        logger.error(f"Error sending help: {str(e)}", exc_info=True)


async def handle_unknown_intent(phone_number: str, message: str):
    """Handle unknown intent"""
    try:
        from services.twilio_service import twilio_service
        
        response = """❓ I didn't understand that.

Try:
• "Send $20 to John" - Send money
• "Balance" - Check balance
• "Help" - See all commands

Or just type what you want to do!
        """
        
        twilio_service.send_message(phone_number, response)
        logger.info(f"Sent unknown intent response to {phone_number}")
    
    except Exception as e:
        logger.error(f"Error handling unknown intent: {str(e)}", exc_info=True)


@app.post("/api/verify-code")
async def verify_code_endpoint(
    phone_number: str,
    code: str
):
    """
    API endpoint for code verification
    (Can be called by web interface or directly)
    """
    try:
        workflow_id = f"registration-{phone_number}"
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Send verification signal
        await handle.signal(RegistrationWorkflow.verify_code, code)
        
        logger.info(f"Sent verification code to workflow for {phone_number}")
        
        return {"success": True, "message": "Code verification submitted"}
    
    except Exception as e:
        logger.error(f"Error verifying code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to verify code")


@app.post("/api/set-pin")
async def set_pin_endpoint(
    phone_number: str,
    pin_hash: str,
    token: str
):
    """
    API endpoint for PIN setup
    (Called by NextJS web portal)
    """
    try:
        workflow_id = f"registration-{phone_number}"
        
        logger.info(f"Attempting to set PIN for {phone_number}, workflow: {workflow_id}")
        
        handle = temporal_client.get_workflow_handle(workflow_id)
        
        # Send PIN setup signal with both parameters as a dict or tuple
        await handle.signal(RegistrationWorkflow.set_pin, {"pin_hash": pin_hash, "token": token})
        
        logger.info(f"Sent PIN setup to workflow for {phone_number}")
        
        return {"success": True, "message": "PIN setup submitted"}
    
    except Exception as e:
        logger.error(f"Error setting PIN: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to set PIN: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)