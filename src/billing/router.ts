import { Router } from 'express';
import Stripe from 'stripe';
import { verifyPaystackSignature } from './paystack.js';
import { pool } from '../db.js';
import type { PoolClient } from 'pg';

export const router = Router();

const stripeSecret = process.env.STRIPE_SECRET;
const stripeWebhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
const stripe = stripeSecret ? new Stripe(stripeSecret, { apiVersion: '2024-06-20' }) : null;

router.post('/stripe/webhook', expressRawJson(), async (req, res) => {
  if (!stripe || !stripeWebhookSecret) return res.status(501).end();
  const sig = req.headers['stripe-signature'] as string;
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, stripeWebhookSecret);
  } catch (err) {
    return res.status(400).send(`Webhook Error: ${(err as Error).message}`);
  }
  const object: any = event.data?.object as any;
  const customerId: string | undefined = typeof object?.customer === 'string' ? object.customer : object?.customer?.id;
  let tenantId: string | null = null;
  if (customerId) {
    const { rows } = await pool.query('select id from tenants where billing_provider = $1 and billing_customer_id = $2', ['stripe', customerId]);
    tenantId = rows[0]?.id ?? null;
  }
  // Handle event types as needed; store billing state if desired
  return res.json({ received: true, tenantId });
});

// Paystack webhook
router.post('/paystack/webhook', expressRawJson(), async (req, res) => {
  const secret = process.env.PAYSTACK_WEBHOOK_SECRET;
  if (!secret) return res.status(501).end();
  const signature = req.headers['x-paystack-signature'] as string | undefined;
  const ok = verifyPaystackSignature(secret, req.body, signature);
  if (!ok) return res.status(400).send('Invalid signature');
  const event = JSON.parse(req.body);
  const customer = event?.data?.customer;
  const customerId: string | undefined = customer?.customer_code || customer?.id || customer?.code;
  let tenantId: string | null = null;
  if (customerId) {
    const { rows } = await pool.query('select id from tenants where billing_provider = $1 and billing_customer_id = $2', ['paystack', String(customerId)]);
    tenantId = rows[0]?.id ?? null;
  }
  res.json({ received: true, tenantId });
});

function expressRawJson() {
  // Minimal raw body collector for Stripe webhook
  return (req: any, _res: any, next: any) => {
    let data = '';
    req.setEncoding('utf8');
    req.on('data', (chunk: string) => (data += chunk));
    req.on('end', () => {
      req.body = data;
      next();
    });
  };
}

