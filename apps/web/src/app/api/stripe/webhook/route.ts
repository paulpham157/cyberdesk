import { stripe } from '@/utils/stripe/stripe-server';
import { headers } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { createClient } from '@/utils/supabase/server';

// Define subscription status type using Stripe's type
type SubscriptionStatus = Stripe.Subscription.Status;

// This is your Stripe webhook secret for testing your endpoint locally.
const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

export async function POST(req: NextRequest) {
  const body = await req.text();
  const sig = headers().get('stripe-signature') as string;
  const supabase = createClient();

  let event;

  try {
    event = stripe.webhooks.constructEvent(body, sig, endpointSecret!);
  } catch (err: any) {
    console.error(`Webhook Error: ${err.message}`);
    return NextResponse.json(
      { error: `Webhook Error: ${err.message}` },
      { status: 400 }
    );
  }

  // Helper function to update profile in Supabase
  const updateProfile = async (customerId: string, data: { 
    subscription_status?: SubscriptionStatus;
    [key: string]: any;
  }) => {
    try {
      // First, find the profile with this Stripe customer ID
      const { data: profiles, error: fetchError } = await supabase
        .from('profiles')
        .select('*')
        .eq('stripe_customer_id', customerId)
        .limit(1);

      if (fetchError) {
        console.error('Error fetching profile:', fetchError);
        return;
      }

      if (profiles && profiles.length > 0) {
        const profile = profiles[0];
        
        // Update the profile with new data
        const { error: updateError } = await supabase
          .from('profiles')
          .update(data)
          .eq('id', profile.id);
          
        if (updateError) {
          console.error('Error updating profile:', updateError);
        } else {
          console.log(`Profile ${profile.id} updated successfully`);
        }
      } else {
        console.log(`No profile found for customer ID: ${customerId}`);
      }
    } catch (error) {
      console.error('Error in updateProfile:', error);
    }
  };

  // Handle the event
  try {
    switch (event.type) {
      case 'checkout.session.async_payment_failed': {
        const session = event.data.object;
        console.log('Checkout session async payment failed:', session);
        
        // Handle the failed async payment
        const customerId = session.customer 
          ? (typeof session.customer === 'string' ? session.customer : session.customer.id)
          : null;
          
        if (customerId) {
          await updateProfile(customerId, {
            subscription_status: 'past_due',
            updated_at: new Date()
          });
        }
        break;
      }
      
      case 'checkout.session.async_payment_succeeded': {
        const session = event.data.object;
        console.log('Checkout session async payment succeeded:', session);
        
        // Similar handling to checkout.session.completed
        const customerId = session.customer 
          ? (typeof session.customer === 'string' ? session.customer : session.customer.id)
          : null;
        const subscriptionId = session.subscription
          ? (typeof session.subscription === 'string' ? session.subscription : session.subscription.id)
          : null;
        
        if (customerId && subscriptionId) {
          // Get subscription details
          const subscription = await stripe.subscriptions.retrieve(subscriptionId);
          
          // Update profile with subscription info
          await updateProfile(customerId, {
            stripe_subscription_id: subscriptionId,
            subscription_status: subscription.status,
            current_period_end: new Date(subscription.current_period_end * 1000),
            plan_id: subscription.items.data[0].price.id,
            cancel_at_period_end: subscription.cancel_at_period_end,
            updated_at: new Date()
          });
        }
        break;
      }
        
      case 'checkout.session.completed': {
        const checkoutSession = event.data.object
        console.log('Checkout session completed:', checkoutSession);
        
        // Get customer ID and subscription ID from the session, handling possible null values
        const customerId = checkoutSession.customer 
          ? (typeof checkoutSession.customer === 'string' ? checkoutSession.customer : checkoutSession.customer.id)
          : null;
        const subscriptionId = checkoutSession.subscription
          ? (typeof checkoutSession.subscription === 'string' ? checkoutSession.subscription : checkoutSession.subscription.id)
          : null;
        
        if (customerId && subscriptionId) {
          // Get subscription details
          const subscription = await stripe.subscriptions.retrieve(subscriptionId);
          
          // Update profile with subscription info
          await updateProfile(customerId, {
            stripe_subscription_id: subscriptionId,
            subscription_status: subscription.status,
            current_period_end: new Date(subscription.current_period_end * 1000),
            plan_id: subscription.items.data[0].price.id,
            cancel_at_period_end: subscription.cancel_at_period_end,
            updated_at: new Date()
          });
        }
        break;
      }
      
      case 'customer.created': {
        const customer = event.data.object;
        console.log('Customer created:', customer);
        
        // No specific action needed here as the customer ID will be associated with a profile
        // when they complete checkout or when the user account is created
        break;
      }
      
      case 'customer.deleted': {
        const customer = event.data.object;
        console.log('Customer deleted:', customer);
        
        // Mark the customer as deleted in our system
        await updateProfile(customer.id, {
          subscription_status: 'canceled',
          updated_at: new Date()
        });
        break;
      }
      
      case 'customer.updated': {
        const customer = event.data.object;
        console.log('Customer updated:', customer);
        
        // Update basic customer information
        await updateProfile(customer.id, {
          email: customer.email,
          updated_at: new Date()
        });
        break;
      }
        
      case 'customer.subscription.created': {
        const subscription = event.data.object
        console.log('Subscription created:', subscription);
        
        const customerId = typeof subscription.customer === 'string' 
          ? subscription.customer 
          : subscription.customer.id;
        
        await updateProfile(customerId, {
          stripe_subscription_id: subscription.id,
          subscription_status: subscription.status,
          current_period_end: new Date(subscription.current_period_end * 1000),
          plan_id: subscription.items.data[0].price.id,
          cancel_at_period_end: subscription.cancel_at_period_end,
          updated_at: new Date()
        });
        break;
      }
      
      case 'customer.subscription.paused': {
        const subscription = event.data.object;
        console.log('Subscription paused:', subscription);
        
        const customerId = typeof subscription.customer === 'string' 
          ? subscription.customer 
          : subscription.customer.id;
        
        await updateProfile(customerId, {
          subscription_status: 'paused',
          updated_at: new Date()
        });
        break;
      }
      
      case 'customer.subscription.resumed': {
        const subscription = event.data.object;
        console.log('Subscription resumed:', subscription);
        
        const customerId = typeof subscription.customer === 'string' 
          ? subscription.customer 
          : subscription.customer.id;
        
        await updateProfile(customerId, {
          subscription_status: subscription.status,
          current_period_end: new Date(subscription.current_period_end * 1000),
          updated_at: new Date()
        });
        break;
      }
        
      case 'customer.subscription.updated': {
        const updatedSubscription = event.data.object as Stripe.Subscription;
        console.log('Subscription updated:', updatedSubscription);
        
        const customerId = typeof updatedSubscription.customer === 'string' 
          ? updatedSubscription.customer 
          : updatedSubscription.customer.id;
        
        await updateProfile(customerId, {
          subscription_status: updatedSubscription.status,
          current_period_end: new Date(updatedSubscription.current_period_end * 1000),
          plan_id: updatedSubscription.items.data[0].price.id,
          cancel_at_period_end: updatedSubscription.cancel_at_period_end,
          updated_at: new Date()
        });
        break;
      }
        
      case 'customer.subscription.deleted': {
        const deletedSubscription = event.data.object as Stripe.Subscription;
        console.log('Subscription deleted:', deletedSubscription);
        
        const customerId = typeof deletedSubscription.customer === 'string' 
          ? deletedSubscription.customer 
          : deletedSubscription.customer.id;
        
        await updateProfile(customerId, {
          subscription_status: 'canceled',
          cancel_at_period_end: false,
          updated_at: new Date()
        });
        break;
      }
        
      case 'invoice.paid': {
        const invoice = event.data.object as Stripe.Invoice;
        console.log('Invoice paid:', invoice);
        
        // Only update if this invoice is for a subscription
        if (invoice.subscription && invoice.customer) {
          const subscriptionId = typeof invoice.subscription === 'string' 
            ? invoice.subscription 
            : invoice.subscription.id;
            
          const customerId = typeof invoice.customer === 'string' 
            ? invoice.customer 
            : invoice.customer.id;
          
          const subscription = await stripe.subscriptions.retrieve(subscriptionId);
          
          await updateProfile(customerId, {
            subscription_status: 'active',
            current_period_end: new Date(subscription.current_period_end * 1000),
            updated_at: new Date()
          });
        }
        break;
      }
        
      case 'invoice.payment_failed': {
        const failedInvoice = event.data.object as Stripe.Invoice;
        console.log('Invoice payment failed:', failedInvoice);
        
        if (failedInvoice.customer) {
          const customerId = typeof failedInvoice.customer === 'string' 
            ? failedInvoice.customer 
            : failedInvoice.customer.id;
          
          await updateProfile(customerId, {
            subscription_status: 'past_due',
            updated_at: new Date()
          });
        }
        break;
      }
      default:
        console.log(`Unhandled event type ${event.type}`);
    }
  } catch (error) {
    console.error(`Error processing webhook event ${event.type}:`, error);
  }

  return NextResponse.json({ received: true });
}
