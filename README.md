ArcAgent Project Structure

```
arcagent/
├── docker-compose.yml
├── README.md
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app with Twilio webhooks
│   ├── worker.py               # Temporal worker
│   ├── config.py               # Configuration management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhooks.py         # Twilio webhook endpoints
│   │   └── health.py           # Health check endpoints
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── registration.py     # User registration workflow
│   │   ├── payment.py          # Payment execution workflow
│   │   └── verification.py     # PIN verification workflow
│   │
│   ├── activities/
│   │   ├── __init__.py
│   │   ├── twilio_activities.py    # Send messages, verify
│   │   ├── database_activities.py  # User CRUD operations
│   │   ├── circle_activities.py    # Circle wallet operations (dummy)
│   │   └── arc_activities.py       # Arc blockchain operations (dummy)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── twilio_service.py   # Twilio client wrapper
│   │   ├── message_parser.py   # Parse user intents from messages
│   │   └── security.py         # PIN hashing, nonce generation
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # Logging configuration
│
└── web/                        # NextJS PIN setup portal (Phase 2)
    └── (to be created later)
```

Key Components
1. FastAPI Backend (main.py)

Webhook endpoints for Twilio
Health checks
Integration with Temporal

2. Temporal Workflows

RegistrationWorkflow: Handle user signup flow
PaymentWorkflow: Execute transfers
VerificationWorkflow: PIN setup and validation

3. Activities

Atomic operations for Twilio, database, Circle, Arc
Each activity is idempotent and retryable

4. Message Flow
User (WhatsApp) 
    ↓
Twilio 
    ↓
FastAPI Webhook 
    ↓
Temporal Workflow 
    ↓
Activities (Twilio/DB/Circle/Arc) 
    ↓
Response to User

----------------------------------------------

# First of all, create a Twilio account. Then follow the next steps.


1. Clone and Setup

cp .env.example .env

# Edit .env with your Twilio credentials

2. Replace the config.py(TWILIO_WHATSAPP_NUMBER)/docker-compose.yaml(twilio account details) data with the real one. TODO: remove every harcoded value.

3. Start Services
# Start all services (Postgres, Temporal, Backend, Worker)

docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f worker

4. Access Services

FastAPI Backend: http://localhost:8000
API Docs: http://localhost:8000/docs
Temporal UI: http://localhost:8080

5. Configure Twilio Webhook

First, for local development, use ngrok:

bashngrok http 8000

# Use the ngrok URL in Twilio: https://xxxxx.ngrok.io/webhooks/twilio/incoming

In your Twilio console, set the WhatsApp webhook URL to:
https://your-domain.com/webhooks/twilio/incoming


User Flow
Registration Flow

User sends: Hi or Register
Bot sends 6-digit verification code
User verifies code (auto-detected or via /api/verify-code)
Bot sends PIN setup link
User sets PIN via secure web portal
Bot creates Circle wallet
Bot sends welcome message

Payment Flow

User sends: Send $20 to Alice
Bot parses intent and checks balance
Bot requests confirmation: CONFIRM or CANCEL
User replies: CONFIRM
Bot executes transfer via Circle/Arc
Bot sends transaction receipt