import { Hono } from 'hono';
import { cors } from 'hono/cors';

type Env = {
	AI: Ai;
	BACKEND_API_URL: string;
	BACKEND_API_KEY: string;
	TWILIO_AUTH_TOKEN: string;
};

const app = new Hono<{ Bindings: Env }>();

app.use('/*', cors());

// Tool implementations - these call your FastAPI backend
async function registerUser(env: Env, phoneNumber: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/register`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-API-Key': env.BACKEND_API_KEY,
		},
		body: JSON.stringify({ phone_number: phoneNumber }),
	});
	return await response.json();
}

async function verifyCode(env: Env, phoneNumber: string, workflowId: string, code: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/workflow/verify-code`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-API-Key': env.BACKEND_API_KEY,
		},
		body: JSON.stringify({
			phone_number: phoneNumber,
			workflow_id: workflowId,
			code: code,
		}),
	});
	return await response.json();
}

async function sendMoney(env: Env, phoneNumber: string, amount: number, recipient: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/payment/send`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-API-Key': env.BACKEND_API_KEY,
		},
		body: JSON.stringify({
			phone_number: phoneNumber,
			amount: amount,
			recipient: recipient,
		}),
	});
	return await response.json();
}

async function checkBalance(env: Env, phoneNumber: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/balance/${encodeURIComponent(phoneNumber)}`, {
		method: 'GET',
		headers: {
			'X-API-Key': env.BACKEND_API_KEY,
		},
	});
	return await response.json();
}

async function getTransactionHistory(env: Env, phoneNumber: string, limit: number = 10) {
	const response = await fetch(
		`${env.BACKEND_API_URL}/api/transactions/${encodeURIComponent(phoneNumber)}?limit=${limit}`,
		{
			method: 'GET',
			headers: {
				'X-API-Key': env.BACKEND_API_KEY,
			},
		}
	);
	return await response.json();
}

async function confirmAction(env: Env, phoneNumber: string, workflowId: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/workflow/confirm`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-API-Key': env.BACKEND_API_KEY,
		},
		body: JSON.stringify({
			phone_number: phoneNumber,
			workflow_id: workflowId,
		}),
	});
	return await response.json();
}

async function cancelAction(env: Env, phoneNumber: string, workflowId: string) {
	const response = await fetch(`${env.BACKEND_API_URL}/api/workflow/cancel`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-API-Key': env.BACKEND_API_KEY,
		},
		body: JSON.stringify({
			phone_number: phoneNumber,
			workflow_id: workflowId,
		}),
	});
	return await response.json();
}

// Main webhook endpoint from Twilio
app.post('/webhook/whatsapp', async (c) => {
	try {
		const formData = await c.req.formData();
		const from = formData.get('From') as string;
		const body = formData.get('Body') as string;
		const messageSid = formData.get('MessageSid') as string;

		// Extract phone number without whatsapp: prefix
		const phoneNumber = from.replace('whatsapp:', '');

		console.log({
			from: phoneNumber,
			message: body,
			messageSid,
		});

		// Build conversation messages
		const messages: any[] = [
			{
				role: 'system',
				content: `You are ArcAgent, a conversational AI financial assistant for USDC payments on WhatsApp.

IMPORTANT WORKFLOW RULES:
1. When a new user says "Hi", "Hello", "Register", or similar greetings, call registerUser tool IMMEDIATELY
2. After registration starts, the user will receive a verification code via WhatsApp (sent by the backend)
3. When user sends a 6-digit number, call verifyCode tool with the code and workflow ID "registration-${phoneNumber}"
4. Do NOT call sendMoney or other tools until the user is registered
5. When user wants to send money, ONLY call sendMoney tool with the exact amount and recipient

Your capabilities:
- Help users register and set up their wallet (use registerUser tool)
- Verify registration codes (use verifyCode tool)
- Send USDC payments to recipients (use sendMoney tool)
- Check wallet balance (use checkBalance tool)
- View transaction history (use getTransactionHistory tool)
- Confirm or cancel pending transactions (use confirmAction/cancelAction tools)

Guidelines:
- Be friendly, concise, and helpful
- For greetings from new users, call registerUser immediately
- When you see a 6-digit code after registration, call verifyCode
- Always specify amounts clearly with $ symbol
- ONLY use the provided tools - never invent tool names
- Check if user is registered before allowing payments

Current user phone: ${phoneNumber}`,
			},
			{
				role: 'user',
				content: body,
			},
		];

		// Define tools available to the AI
		const tools = [
			{
				name: 'registerUser',
				description: 'Register a new user and start the onboarding process with verification code',
				parameters: {
					type: 'object',
					properties: {},
					required: [],
				},
			},
			{
				name: 'verifyCode',
				description: 'Verify the 6-digit code sent to user during registration',
				parameters: {
					type: 'object',
					properties: {
						code: {
							type: 'string',
							description: 'The 6-digit verification code',
						},
						workflowId: {
							type: 'string',
							description: 'The registration workflow ID',
						},
					},
					required: ['code', 'workflowId'],
				},
			},
			{
				name: 'sendMoney',
				description: 'Initiate a USDC payment to a recipient. This will request confirmation from the user.',
				parameters: {
					type: 'object',
					properties: {
						amount: {
							type: 'number',
							description: 'The amount in USD to send (e.g., 20.50)',
						},
						recipient: {
							type: 'string',
							description: 'The recipient identifier (name, phone number, or wallet address)',
						},
					},
					required: ['amount', 'recipient'],
				},
			},
			{
				name: 'checkBalance',
				description: 'Check the current USDC balance in the user wallet',
				parameters: {
					type: 'object',
					properties: {},
					required: [],
				},
			},
			{
				name: 'getTransactionHistory',
				description: 'Get recent transaction history for the user',
				parameters: {
					type: 'object',
					properties: {
						limit: {
							type: 'number',
							description: 'Number of transactions to retrieve (default 10)',
						},
					},
					required: [],
				},
			},
			{
				name: 'confirmAction',
				description: 'Confirm a pending action (payment, etc.)',
				parameters: {
					type: 'object',
					properties: {
						workflowId: {
							type: 'string',
							description: 'The workflow ID to confirm',
						},
					},
					required: ['workflowId'],
				},
			},
			{
				name: 'cancelAction',
				description: 'Cancel a pending action',
				parameters: {
					type: 'object',
					properties: {
						workflowId: {
							type: 'string',
							description: 'The workflow ID to cancel',
						},
					},
					required: ['workflowId'],
				},
			},
		];

		// Run AI with tools
		let result: AiTextGenerationOutput = await c.env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
			messages,
			tools,
		});

		// Process tool calls iteratively
		let iterationCount = 0;
		const maxIterations = 5;

		while (result.tool_calls && result.tool_calls.length > 0 && iterationCount < maxIterations) {
			iterationCount++;

			// Process all tool calls in this iteration
			for (const toolCall of result.tool_calls) {
				let fnResponse;

				try {
					switch (toolCall.name) {
						case 'registerUser':
							fnResponse = await registerUser(c.env, phoneNumber);
							break;

						case 'verifyCode':
							fnResponse = await verifyCode(
								c.env,
								phoneNumber,
								(toolCall.arguments as any).workflowId,
								(toolCall.arguments as any).code
							);
							break;

						case 'sendMoney':
							fnResponse = await sendMoney(
								c.env,
								phoneNumber,
								(toolCall.arguments as any).amount,
								(toolCall.arguments as any).recipient
							);
							break;

						case 'checkBalance':
							fnResponse = await checkBalance(c.env, phoneNumber);
							break;

						case 'getTransactionHistory':
							fnResponse = await getTransactionHistory(
								c.env,
								phoneNumber,
								(toolCall.arguments as any).limit || 10
							);
							break;

						case 'confirmAction':
							fnResponse = await confirmAction(c.env, phoneNumber, (toolCall.arguments as any).workflowId);
							break;

						case 'cancelAction':
							fnResponse = await cancelAction(c.env, phoneNumber, (toolCall.arguments as any).workflowId);
							break;

						default:
							fnResponse = { error: `Unknown tool: ${toolCall.name}` };
							break;
					}
				} catch (error) {
					fnResponse = { error: `Tool execution failed: ${error}` };
				}

				console.log({
					tool: toolCall.name,
					arguments: toolCall.arguments,
					response: fnResponse,
				});

				// Add tool response to messages
				messages.push({
					role: 'tool',
					name: toolCall.name,
					content: JSON.stringify(fnResponse),
				});
			}

			// Get next AI response with tool results
			result = await c.env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
				messages,
				tools,
			});
		}

		// Get final assistant message
		let responseText = result.response || 'I encountered an issue processing your request.';

		// Send response back to user via Twilio
		await fetch(`${c.env.BACKEND_API_URL}/api/send-message`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-API-Key': c.env.BACKEND_API_KEY,
			},
			body: JSON.stringify({
				to: phoneNumber,
				message: responseText,
			}),
		});

		// Return TwiML response (empty since we're sending via API)
		return c.text('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {
			'Content-Type': 'text/xml',
		});
	} catch (error) {
		console.error('Webhook error:', error);
		return c.text('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {
			'Content-Type': 'text/xml',
		});
	}
});

// Health check endpoint
app.get('/health', (c) => {
	return c.json({ status: 'ok', timestamp: new Date().toISOString() });
});

export default app;