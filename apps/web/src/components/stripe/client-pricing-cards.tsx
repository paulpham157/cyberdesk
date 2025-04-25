"use client";

import { Container } from '@/components/container';
import { Gradient } from '@/components/gradient';
import type { User } from '@supabase/supabase-js';
import type { Profile } from '@/types/database';
import { PricingCard } from './client-pricing-card';
import { useEffect, useState } from 'react';
import { supabase } from '@/utils/supabaseClient';
import { Subheading } from '@/components/text';
import CONFIG from '../../../config';

// Define the tier type
interface Tier {
  name: string;
  slug: string;
  description: string;
  priceMonthly: number;
  href: string;
  highlights: { description: string; disabled?: boolean }[];
  features: any[];
}

export default function ClientPricingCards({ 
  tiers,
  user,
  profile
}: { 
  tiers: Tier[];
  user: User | null;
  profile: Profile | null;
}) {
  const [activeSubscriptionsCount, setActiveSubscriptionsCount] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const SUBSCRIPTION_LIMIT = CONFIG.subscriptionLimit;
  
  useEffect(() => {
    // Only check subscription count for logged-in users
    if (user) {
      async function fetchActiveSubscriptions() {
        try {
          setIsLoading(true);
          const { count, error } = await supabase
            .from('profiles')
            .select('*', { count: 'exact', head: true })
            .eq('subscription_status', 'active');
            
          if (error) {
            console.error('Error fetching active subscriptions:', error);
          } else {
            setActiveSubscriptionsCount(count);
          }
        } catch (err) {
          console.error('Error in fetchActiveSubscriptions:', err);
        } finally {
          setIsLoading(false);
        }
      }
      
      fetchActiveSubscriptions();
    }
  }, [user]);
  
  const isSoldOut = user && activeSubscriptionsCount !== null && activeSubscriptionsCount >= SUBSCRIPTION_LIMIT;
  
  // Custom component for sold-out tier card
  const SoldOutPricingCard = ({ tier }: { tier: Tier }) => (
    <div className="-m-2 grid grid-cols-1 rounded-4xl ring-1 shadow-[inset_0_0_2px_1px_#ffffff4d] ring-black/5 max-lg:mx-auto max-lg:w-full max-lg:max-w-sm">
      <div className="grid grid-cols-1 rounded-4xl p-2 shadow-md shadow-black/5">
        <div className="rounded-3xl bg-white p-10 pb-9 ring-1 shadow-2xl ring-black/5">
          <Subheading>{tier.name}</Subheading>
          <p className="mt-2 text-sm/6 text-gray-950/75">{tier.description}</p>
          <div className="mt-8 flex items-center gap-4">
            <div className="text-5xl font-medium text-gray-950">
              ${tier.priceMonthly}
            </div>
            <div className="text-sm/5 text-gray-950/75">
              <p>USD</p>
              <p>per month</p>
            </div>
          </div>
          <div className="mt-8">
            <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-md">
              <p className="font-medium">Thank you for your interest!</p>
              <p className="mt-1 text-sm">We&apos;re sold out but we&apos;re working on adding more capacity!</p>
            </div>
          </div>
          <div className="mt-8">
            <h3 className="text-sm/6 font-medium text-gray-950">
              You get access to:
            </h3>
            <ul className="mt-3 space-y-3">
              {tier.highlights.map((props, featureIndex) => (
                <li key={featureIndex} className={`flex gap-3 ${props.disabled ? 'text-gray-950/50' : 'text-gray-950/80'}`}>
                  <span className="inline-flex h-6 items-center">
                    <svg viewBox="0 0 15 15" className="size-[0.9375rem] shrink-0 fill-gray-950/25" aria-hidden="true">
                      <path clipRule="evenodd" d="M8 0H7v7H0v1h7v7h1V8h7V7H8V0z" />
                    </svg>
                  </span>
                  {props.disabled && <span className="sr-only">Not included:</span>}
                  {props.description}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="relative py-24">
      <Gradient className="absolute inset-x-2 top-48 bottom-0 rounded-4xl ring-1 ring-black/5 ring-inset" />
      <Container className="relative">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {tiers.map((tier, tierIndex) => {
            // If user is logged in and subscriptions are sold out, show sold out message
            if (isSoldOut) {
              return <SoldOutPricingCard key={tierIndex} tier={tier} />;
            }
            
            // Otherwise show normal pricing card
            return (
              <PricingCard 
                key={tierIndex} 
                tier={tier} 
                user={user} 
                profile={profile} 
              />
            );
          })}
        </div>
      </Container>
    </div>
  );
}
