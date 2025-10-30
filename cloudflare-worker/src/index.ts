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

// In-memory storage for user context (workflow IDs, etc.)
// In production, use KV storage or database
const userContext = new Map<string, { lastWorkflowId?: string; lastWorkflowType?: string }>();

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

		// Get user context
		let context = userContext.get(phoneNumber) || {};

		// Build conversation messages
		const messages: any[] = [
			{
				role: 'system',
				content: `You are ArcAgent, a friendly AI assistant for USDC payments on WhatsApp.

RULES:
- Call tools silently without explaining what you're doing
- Never say "I will call" or "Tool call" - just call the tool and respond based on the result
- Be conversational and natural in your responses
- Only use confirmAction/cancelAction when there's an active payment workflow

CONTEXT:
- Last workflow: ${context.lastWorkflowId || 'none'}
- Workflow type: ${context.lastWorkflowType || 'none'}

TOOL USAGE:
- "Hi/Hello/Register" → registerUser
- 6-digit code → verifyCode with workflow "registration-${phoneNumber}"
- "Send $X to Y" → sendMoney (creates payment workflow)
- "Balance/How much" → checkBalance
- "Transactions/History" → getTransactionHistory
- "CONFIRM" → confirmAction (only if lastWorkflowType is 'payment')
- "CANCEL" → cancelAction (only if lastWorkflowType is 'payment')

Be helpful and concise. Don't explain your tool calls to the user.`,
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

		// Process tool calls - only process ONCE
		if (result.tool_calls && result.tool_calls.length > 0) {
			// Process only the FIRST tool call to avoid duplicates
			const toolCall = result.tool_calls[0];
			let fnResponse;

			try {
				switch (toolCall.name) {
					case 'registerUser':
						fnResponse = await registerUser(c.env, phoneNumber);
						if (fnResponse.success && fnResponse.workflow_id) {
							context.lastWorkflowId = fnResponse.workflow_id;
							context.lastWorkflowType = 'registration';
						}
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
						if (fnResponse.success && fnResponse.workflow_id) {
							context.lastWorkflowId = fnResponse.workflow_id;
							context.lastWorkflowType = 'payment';
						}
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
						const confirmWorkflowId = (toolCall.arguments as any).workflowId || context.lastWorkflowId;
						// Only allow confirmation if there's an active payment workflow
						if (!confirmWorkflowId || context.lastWorkflowType !== 'payment') {
							fnResponse = { success: false, error: 'No pending payment to confirm. Say "Send $X to Y" to start a payment.' };
						} else {
							fnResponse = await confirmAction(c.env, phoneNumber, confirmWorkflowId);
							// Clear context after confirmation
							context.lastWorkflowId = undefined;
							context.lastWorkflowType = undefined;
						}
						break;

					case 'cancelAction':
						const cancelWorkflowId = (toolCall.arguments as any).workflowId || context.lastWorkflowId;
						// Only allow cancellation if there's an active payment workflow
						if (!cancelWorkflowId || context.lastWorkflowType !== 'payment') {
							fnResponse = { success: false, error: 'No pending payment to cancel.' };
						} else {
							fnResponse = await cancelAction(c.env, phoneNumber, cancelWorkflowId);
							// Clear context after cancellation
							context.lastWorkflowId = undefined;
							context.lastWorkflowType = undefined;
						}
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

			// Save updated context
			userContext.set(phoneNumber, context);

			// Add tool response to messages
			messages.push({
				role: 'tool',
				name: toolCall.name,
				content: JSON.stringify(fnResponse),
			});

			// Get AI response with tool result
			result = await c.env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
				messages,
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