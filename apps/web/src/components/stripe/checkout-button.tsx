"use client";

import { useState } from 'react';
import { Button } from '@/components/button';
import type { User } from '@supabase/supabase-js';
import type { Profile } from '@/types/database';
import type { Tier } from '@/config/tiers';

export interface CheckoutButtonProps {
  tier: Tier;
  user: User | null;
  profile: Profile | null;
  children?: React.ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "outline";
}

export function CheckoutButton({ 
  tier, 
  user, 
  profile,
  children,
  className,
  variant
}: CheckoutButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  
  // Determine the button text based on user authentication and subscription status
  let buttonText = children || 'Start a free trial';
  let buttonAction: 'link' | 'checkout' | 'disabled' = 'link';
  let buttonHref = tier.href;
  
  if (!user) {
    // User is not logged in
    buttonText = children || 'Get Started';
    buttonHref = '/login';
    buttonAction = 'link';
  } else if (profile && profile.subscription_status === 'active') {
    // User is logged in and has an active subscription
    buttonText = children || 'You are already subscribed to this plan';
    buttonAction = 'disabled';
  } else if (user) {
    // User is logged in but not subscribed
    buttonText = children || `Subscribe to ${tier.name}`;
    buttonAction = 'checkout';
  }
  
  const handleCheckout = async () => {
    try {
      setIsLoading(true);
      
      const response = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // You can customize success and cancel URLs if needed
          successUrl: `${window.location.origin}/dashboard?payment=success`,
          cancelUrl: `${window.location.origin}/pricing?payment=cancelled`,
          stripeCustomerId: profile?.stripe_customer_id || null,
        }),
      });

      const { url } = await response.json();
      
      if (url) {
        window.location.href = url;
      } else {
        throw new Error('Failed to create checkout session');
      }
    } catch (error) {
      console.error('Error during checkout:', error);
      alert('Something went wrong. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {buttonAction === 'disabled' ? (
        <div className={`inline-flex items-center justify-center w-full rounded-md px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 cursor-not-allowed ${className || ''}`}>
          {buttonText}
        </div>
      ) : buttonAction === 'checkout' ? (
        <Button 
          onClick={handleCheckout}
          disabled={isLoading}
          className={className}
          variant={variant}
        >
          {isLoading ? 'Processing...' : buttonText}
        </Button>
      ) : (
        <Button href={buttonHref} className={className} variant={variant}>
          {buttonText}
        </Button>
      )}
    </>
  );
}
