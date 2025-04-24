"use client";

import { useState } from 'react';
import { Button } from '@/components/button';
import { Subheading } from '@/components/text';
import type { User } from '@supabase/supabase-js';
import type { Profile } from '@/types/database';
import { CheckoutButton } from './checkout-button';

// Import the FeatureItem component from the same file
function FeatureItem({
  description,
  disabled = false,
}: {
  description: string;
  disabled?: boolean;
}) {
  return (
    <li
      className={`flex gap-3 ${
        disabled ? 'text-gray-950/50' : 'text-gray-950/80'
      }`}
    >
      <span className="inline-flex h-6 items-center">
        <PlusIcon className="size-[0.9375rem] shrink-0 fill-gray-950/25" />
      </span>
      {disabled && <span className="sr-only">Not included:</span>}
      {description}
    </li>
  );
}

function PlusIcon(props: React.ComponentPropsWithoutRef<'svg'>) {
  return (
    <svg viewBox="0 0 15 15" aria-hidden="true" {...props}>
      <path clipRule="evenodd" d="M8 0H7v7H0v1h7v7h1V8h7V7H8V0z" />
    </svg>
  );
}

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

export function PricingCard({ 
  tier, 
  user, 
  profile 
}: { 
  tier: Tier; 
  user: User | null; 
  profile: Profile | null;
}) {
  return (
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
            <CheckoutButton tier={tier} user={user} profile={profile} />
          </div>
          <div className="mt-8">
            <h3 className="text-sm/6 font-medium text-gray-950">
              You get access to:
            </h3>
            <ul className="mt-3 space-y-3">
              {tier.highlights.map((props, featureIndex) => (
                <FeatureItem key={featureIndex} {...props} />
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
