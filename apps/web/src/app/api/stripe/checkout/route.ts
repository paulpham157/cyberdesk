import { stripe, STRIPE_PRICE_ID } from '@/utils/stripe-server';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { successUrl, cancelUrl, stripeCustomerId } = await req.json();
    
    // Create a Stripe checkout session for the Pro plan
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price: STRIPE_PRICE_ID,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: successUrl || `${req.nextUrl.origin}/dashboard?payment=success`,
      cancel_url: cancelUrl || `${req.nextUrl.origin}/pricing?payment=cancelled`,
      metadata: {
        plan: 'pro',
      },
      ...(stripeCustomerId && { customer: stripeCustomerId }),
    });

    return NextResponse.json({ sessionId: session.id, url: session.url });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    return NextResponse.json(
      { error: 'Error creating checkout session' },
      { status: 500 }
    );
  }
}
