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
├── frontend/                        # NextJS
│    ├──app/
│    ├──public/
│    └──package.json
│
└── cloudflare-worker
    ├──src/
    ├──package.json
    └──wrangler.toml
```

Key Components
1. FastAPI Backend (main.py)
```
Webhook endpoints for Twilio
Health checks
Integration with Temporal
```

2. Temporal Workflows
```
RegistrationWorkflow: Handle user signup flow
PaymentWorkflow: Execute transfers
VerificationWorkflow: PIN setup and validation
```

3. Activities
```
Atomic operations for Twilio, database, Circle, Arc
Each activity is idempotent and retryable
```

4. Message Flow
```
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
```
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

ngrok http 8000

# Use the ngrok URL in Twilio: https://xxxxx.ngrok.io/webhooks/twilio/incoming

In your Twilio console, set the WhatsApp webhook URL to:
https://your-domain.com/webhooks/twilio/incoming


User Flow
Registration Flow

```
User sends: Hi or Register
Bot sends 6-digit verification code and it gets auto-detected
Bot sends PIN setup link
User sets PIN via secure web portal
Bot creates Circle wallet
Bot sends welcome message
```

Payment Flow

```
User sends: Send $20 to Alice
Bot parses intent and checks balance
Bot requests confirmation: CONFIRM or CANCEL
User replies: CONFIRM
Bot executes transfer via Circle/Arc
Bot sends transaction receipt
```

-----------------------------------------------------------------------------------

# Getting Started - Step by Step
Prerequisites
Before you begin, ensure you have:

Node.js (v18+) and npm
Python (3.11+) and pip
Docker and Docker Compose
Git

# Required Accounts & API Keys
You'll need to create accounts and obtain API keys from:

Twilio (WhatsApp messaging)
Circle (Web3 Services - wallet management)
Cloudflare (Workers AI)


# Step-by-Step Setup
Step 1: Clone the Repository

Step 2: Set Up Twilio WhatsApp

Create Twilio Account: Go to twilio.com and sign up
Enable WhatsApp Sandbox:

Navigate to Messaging > Try it out > Send a WhatsApp message
Follow instructions to connect your WhatsApp to the sandbox
Note down your sandbox number (e.g., +1 415 523 8886)


Get Credentials:

Account SID: Found on your Console Dashboard
Auth Token: Also on the Dashboard (click to reveal)
WhatsApp Number: Your sandbox number in format whatsapp:+14155238886

Step 3: Set Up Circle Developer Account

Create Circle Account: Go to circle.com/developers
Access Developer Console: Navigate to console.circle.com
Create API Key:

Go to Programmable Wallets > Developer Controlled
Click Create API Key
Save the API Key immediately (shown only once)

Get Entity Secret:

In the same section, find your Entity Secret
Copy and save it securely

Note Token ID:

Default USDC token on Arc Testnet: 0x3600000000000000000000000000000000000000

Step 4: Set Up Cloudflare Workers

Create Cloudflare Account: Go to cloudflare.com
Install Wrangler CLI:

npm install -g wrangler

Login to Cloudflare:

wrangler login

Enable Workers AI:

Go to your Cloudflare Dashboard
Navigate to Workers & Pages > AI
Enable Workers AI

Step 5: Configure Environment Variables

Create backend .env file:

cd backend
cp .env.example .env

Edit backend/.env with your credentials:
```
   # Twilio Configuration
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_NUMBER=your_twilio_number
   
   # Circle Configuration
   CIRCLE_API_KEY=your_circle_api_key_here
   CIRCLE_ENTITY_SECRET=your_entity_secret_here
   CIRCLE_USDC_TOKEN_ID=0x3600000000000000000000000000000000000000
   
   # Security (generate secure random strings)
   BACKEND_API_KEY=your_secure_random_key_here
   PIN_SALT=your_secure_random_salt_here
   SESSION_SECRET=your_secure_session_secret_here
   
   # Database (default for local development)
   DATABASE_URL=postgresql://arcagent:arcagent_dev_password@localhost:5432/arcagent
   
   # Temporal
   TEMPORAL_HOST=localhost:7233
   TEMPORAL_TASK_QUEUE=arcagent-task-queue
   
   # Environment
   ENVIRONMENT=development
   LOG_LEVEL=INFO
```

Configure Cloudflare Worker:

```
cd cloudflare-worker
```

Edit wrangler.toml:
```
   name = "arcagent-ai-worker"
   main = "src/index.ts"
   compatibility_date = "2024-01-01"
   
   [ai]
   binding = "AI"
   
   [vars]
   BACKEND_API_URL = "http://localhost:8000"
   BACKEND_API_KEY = "your_secure_random_key_here"
```

Step 6: Install Dependencies

Backend dependencies:
cd backend
pip install -r requirements.txt

Cloudflare Worker dependencies:
cd ../cloudflare-worker
npm install

Step 7: Start the Infrastructure

Start all services (PostgreSQL, Temporal, Backend, Worker):
cd ..
docker-compose up -d

Verify services are running:
docker-compose ps
You should see:

```
✅ postgres - Database
✅ temporal - Workflow engine
✅ temporal-ui - Web UI at http://localhost:8080
✅ backend - FastAPI at http://localhost:8000
✅ worker - Temporal worker
```

Check logs:

docker-compose logs -f backend
docker-compose logs -f worker
Step 8: Deploy Cloudflare Worker

Deploy to Cloudflare:

   cd cloudflare-worker
   wrangler deploy

Note your Worker URL (e.g., https://arcagent-ai-worker.your-subdomain.workers.dev)
For production, update backend .env with your Worker URL:

CLOUDFLARE_WORKER_URL=https://arcagent-ai-worker.your-subdomain.workers.dev

Restart backend:

   docker-compose restart backend worker
```

### Step 9: Configure Twilio Webhook

1. **Go to Twilio Console** > **Messaging > Try it out > WhatsApp Sandbox Settings**
2. **Set "When a message comes in" webhook**:
```
   https://ngrok.url/webhook/whatsapp

Method: POST
Save the configuration

Step 10: Test the System

Send "Hi" to your Twilio WhatsApp number
You should receive: Auto-verification success and a PIN setup link
Click the link and set your 6-digit PIN
Wait for confirmation: "Welcome to ArcAgent! Your wallet is ready!"

Test basic commands:

Balance - Check your wallet balance
Send $5 to +1234567890 - Initiate a payment
CONFIRM - Confirm the payment
Transactions - View transaction history


Troubleshooting
Services won't start
# Check Docker logs
docker-compose logs

# Restart all services
docker-compose down
docker-compose up -d
Worker deployment fails
# Verify you're logged in
wrangler whoami

# Check wrangler.toml configuration
cat wrangler.toml

# Try deploying with verbose output
wrangler deploy --verbose
Backend can't connect to Temporal
# Check if Temporal is running
docker-compose ps temporal

# Check Temporal logs
docker-compose logs temporal

# Restart Temporal
docker-compose restart temporal
Twilio webhook not receiving messages

Verify webhook URL is publicly accessible (use ngrok for local testing)
Check Cloudflare Worker logs: wrangler tail
Verify BACKEND_API_KEY matches in both backend and worker

Circle API errors

Verify API key and entity secret are correct
Check Circle Dashboard for rate limits
Ensure you're using testnet credentials


Using ngrok for Local Development
If testing locally, you'll need to expose your Cloudflare Worker:
# Install ngrok
npm install -g ngrok

# Expose your LLM
ngrok http 8787

# Use the ngrok URL in Twilio webhook configuration

Monitoring & Debugging

Temporal UI: http://localhost:8080
Backend API Docs: http://localhost:8000/docs
Backend Health: http://localhost:8000/health
Worker Logs: wrangler tail (after deployment)
Backend Logs: docker-compose logs -f backend
Worker Logs: docker-compose logs -f worker