from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import PlainTextResponse, HTMLResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from temporalio.client import Client
from datetime import datetime
import logging

from config import settings
from models.database import init_db, get_db, User, Transaction
from workflows import RegistrationWorkflow, PaymentWorkflow
from services import twilio_service, circle_service
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

app = FastAPI(title="ArcAgent API")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")


# Dependency for API key authentication
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from Cloudflare Worker"""
    expected_key = settings.BACKEND_API_KEY
    if x_api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# Pydantic models
class RegisterRequest(BaseModel):
    phone_number: str

class VerifyCodeRequest(BaseModel):
    phone_number: str
    workflow_id: str
    code: str
    
class SetPinRequest(BaseModel):
    phone_number: str
    workflow_id: str
    pin_hash: str
    token: str    

class SendMoneyRequest(BaseModel):
    phone_number: str
    amount: float
    recipient: str


class WorkflowActionRequest(BaseModel):
    phone_number: str
    workflow_id: str


class SendMessageRequest(BaseModel):
    to: str
    message: str


# Helper to get Temporal client
async def get_temporal_client() -> Client:
    """Get Temporal client instance"""
    return await Client.connect(settings.TEMPORAL_HOST)


# ============ API ENDPOINTS ============

@app.post("/api/register")
async def register_user(
    request: RegisterRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Start user registration workflow
    
    This initiates the Temporal workflow that:
    1. Creates user in database
    2. Sends verification code
    3. Waits for verification
    4. Sets up PIN
    5. Creates Circle wallet
    """
    try:
        client = await get_temporal_client()
        
        workflow_id = f"registration-{request.phone_number}"
        
        try:
            handle = await client.start_workflow(
                RegistrationWorkflow.run,
                request.phone_number,
                id=workflow_id,
                task_queue=settings.TEMPORAL_TASK_QUEUE,
            )
            
            logger.info(f"Started registration workflow for {request.phone_number}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "message": "Registration started. Check your WhatsApp for verification code.",
            }
            
        except Exception as e:
            if "already started" in str(e).lower():
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "message": "Registration already in progress. Please complete the steps sent to your WhatsApp.",
                }
            raise
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start registration. Please try again.",
        }

@app.post("/api/workflow/verify-code")
async def verify_code_workflow(
    request: VerifyCodeRequest,
    api_key: str = Depends(verify_api_key)
):
    """Send verification code to registration workflow"""
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)
        
        await handle.signal("verify_code", request.code)
        
        return {
            "success": True,
            "message": "Code verified successfully",
        }
        
    except Exception as e:
        logger.error(f"Code verification error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to verify code.",
        }
        
@app.post("/api/workflow/set-pin")
async def set_pin_workflow(
    request: SetPinRequest,
    api_key: str = Depends(verify_api_key)
):
    """Send PIN setup signal to registration workflow"""
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)
        
        await handle.signal("set_pin", {
            "pin_hash": request.pin_hash,
            "token": request.token
        })
        
        logger.info(f"PIN setup signal sent for {request.phone_number}")
        
        return {
            "success": True,
            "message": "PIN set successfully",
        }
        
    except Exception as e:
        logger.error(f"PIN setup error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set PIN.",
        }        
        
@app.post("/api/payment/send")
async def send_money(
    request: SendMoneyRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Initiate payment workflow
    
    This starts a Temporal workflow that:
    1. Validates user and balance
    2. Requests confirmation
    3. Executes transfer via Circle
    4. Sends receipt
    """
    try:
        user = db.query(User).filter(User.whatsapp_number == request.phone_number).first()
        if not user or not user.registration_completed:
            return {
                "success": False,
                "error": "user_not_registered",
                "message": "You need to register first. Send 'Hi' to get started.",
            }
        
        if request.amount <= 0:
            return {
                "success": False,
                "error": "invalid_amount",
                "message": "Amount must be greater than zero.",
            }
        
        client = await get_temporal_client()
        
        workflow_id = f"payment-{request.phone_number}-{int(datetime.now().timestamp())}"
        
        handle = await client.start_workflow(
            PaymentWorkflow.run,
            args=[request.phone_number, request.amount, request.recipient],
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )
        
        logger.info(f"Started payment workflow {workflow_id}")
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": f"Payment of ${request.amount:.2f} to {request.recipient} initiated. Please confirm when prompted.",
            "amount": request.amount,
            "recipient": request.recipient,
        }
        
    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process payment. Please try again.",
        }


@app.get("/api/balance/{phone_number}")
async def check_balance(
    phone_number: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get user's wallet balance"""
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user or not user.registration_completed:
            return {
                "success": False,
                "error": "user_not_registered",
                "message": "You need to register first.",
            }
        
        from activities.circle_activities import get_wallet_balance
        balance = await get_wallet_balance(user.circle_wallet_id)
        
        return {
            "success": True,
            "balance": balance,
            "wallet_address": user.circle_wallet_address,
            "message": f"Your balance is ${balance:.2f} USDC",
        }
        
    except Exception as e:
        logger.error(f"Balance check error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to check balance.",
        }


@app.get("/api/transactions/{phone_number}")
async def get_transactions(
    phone_number: str,
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get transaction history"""
    try:
        user = db.query(User).filter(User.whatsapp_number == phone_number).first()
        
        if not user:
            return {
                "success": False,
                "error": "user_not_found",
                "transactions": [],
            }
        
        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == phone_number)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .all()
        )
        
        tx_list = [
            {
                "id": tx.id,
                "type": tx.transaction_type,
                "amount": tx.amount,
                "recipient": tx.recipient,
                "status": tx.status,
                "tx_hash": tx.tx_hash,
                "created_at": tx.created_at.isoformat(),
                "confirmed_at": tx.confirmed_at.isoformat() if tx.confirmed_at else None,
            }
            for tx in transactions
        ]
        
        return {
            "success": True,
            "transactions": tx_list,
            "count": len(tx_list),
        }
        
    except Exception as e:
        logger.error(f"Transaction history error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "transactions": [],
        }


@app.post("/api/workflow/confirm")
async def confirm_workflow(
    request: WorkflowActionRequest,
    api_key: str = Depends(verify_api_key)
):
    """Send confirmation signal to workflow"""
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)
        
        if "payment" in request.workflow_id:
            await handle.signal("confirm_payment")
        
        return {
            "success": True,
            "message": "Confirmation sent",
        }
        
    except Exception as e:
        logger.error(f"Confirmation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to confirm action.",
        }


@app.post("/api/workflow/cancel")
async def cancel_workflow(
    request: WorkflowActionRequest,
    api_key: str = Depends(verify_api_key)
):
    """Send cancellation signal to workflow"""
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(request.workflow_id)
        
        if "payment" in request.workflow_id:
            await handle.signal("cancel_payment")
        
        return {
            "success": True,
            "message": "Action cancelled",
        }
        
    except Exception as e:
        logger.error(f"Cancellation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to cancel action.",
        }


@app.post("/api/send-message")
async def send_message(
    request: SendMessageRequest,
    api_key: str = Depends(verify_api_key)
):
    """Send message to user via Twilio"""
    try:
        message_sid = twilio_service.send_message(
            to=request.to if request.to.startswith('whatsapp:') else f'whatsapp:{request.to}',
            body=request.message
        )
        
        return {
            "success": True,
            "message_sid": message_sid,
        }
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
        }


@app.get("/setup-pin", response_class=HTMLResponse)
async def serve_pin_setup():
    """Serve PIN setup page"""
    html_file = Path(__file__).parent.parent / "pin-setup.html"
    return html_file.read_text()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "arcagent-backend",
    }