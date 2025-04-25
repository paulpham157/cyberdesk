import Stripe from 'stripe';

// This file should only be imported in server components or API routes
if (typeof window !== 'undefined') {
  throw new Error('This file should only be imported in server components or API routes');
}

// Initialize Stripe with the secret key from environment variables
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || '', {
  apiVersion: '2025-02-24.acacia', // Use the latest API version
});

// Price ID for the Pro subscription tier
export const STRIPE_PRICE_ID = process.env.STRIPE_PRICE_ID_PRO || '';