'use client'

import { SubscriptionSection } from '@/components/dashboard/subscription-section'
import type { Profile } from '@/types/database'
import { ApiKeyManager } from '@/components/dashboard/api-key-manager'
import { VMInstancesManager } from '@/components/dashboard/vm-instances-manager'
import { supabase } from '@/utils/supabaseClient'
import { ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'
import { PricingCard } from '@/components/stripe/client-pricing-card'
import { tiers } from '@/config/tiers'
import { FAQSection } from '@/components/dashboard/faq-section'
import posthog from 'posthog-js'
import { useEffect, useState } from 'react'
import { Subheading } from '@/components/text'
import CONFIG from '../../../config'

interface DashboardContentProps {
  userEmail?: string;
  userId?: string;
  profile?: Profile | null;
}

export function DashboardContent({ userEmail, userId, profile }: DashboardContentProps) {
  const isSubscriptionActive = profile?.subscription_status === "active";
  const [activeSubscriptionsCount, setActiveSubscriptionsCount] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const SUBSCRIPTION_LIMIT = CONFIG.subscriptionLimit;
  
  useEffect(() => {
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
  }, []);
  
  const handleLogout = async () => {
    // Reset PostHog user to anonymous before logging out
    posthog.reset();
    
    await supabase.auth.signOut();
    window.location.href = '/';
  };
  
  const isSoldOut = activeSubscriptionsCount !== null && activeSubscriptionsCount >= SUBSCRIPTION_LIMIT;
  
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          {isSubscriptionActive ? (
            <>
              <h2 className="text-xl font-medium tracking-tight text-gray-900 sm:text-4xl">Dashboard</h2 >
              <p className="mt-2 text-base/7 text-gray-600">
                Welcome to your dashboard. This is where you can manage your virtual desktops, account settings, and more.
              </p>
            </>
          ) : (
            <>
              <h2 className="text-xl font-medium tracking-tight text-gray-900 sm:text-4xl">Get Started with Cyberdesk</h2>
              <p className="mt-2 text-base/7 text-gray-600">
                Unlock the full power of Cyberdesk by subscribing to our Pro plan.
              </p>
            </>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <ArrowRightOnRectangleIcon className="h-3.5 w-3.5" />
          Sign Out
        </button>
      </div>
      
      {/* For non-active subscribers, show pricing card and FAQ section */}
      {!isSubscriptionActive && (
        <div className="flex flex-col md:flex-row md:space-x-8 space-y-8 md:space-y-0 justify-center">
          <div className="max-w-sm">
            {isLoading ? (
              <div className="animate-pulse rounded-3xl bg-gray-100 p-10 pb-9 h-[450px] flex items-center justify-center">
                <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : isSoldOut ? (
              <div className="rounded-3xl bg-white p-10 pb-9 ring-1 shadow-2xl ring-black/5">
                <Subheading>{tiers[0].name}</Subheading>
                <p className="mt-2 text-sm/6 text-gray-950/75">{tiers[0].description}</p>
                <div className="mt-8 flex items-center gap-4">
                  <div className="text-5xl font-medium text-gray-950">
                    ${tiers[0].priceMonthly}
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
                    {tiers[0].highlights.map((props, featureIndex) => (
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
            ) : (
              <PricingCard 
                tier={tiers[0]} 
                user={userId ? { id: userId } as any : null} 
                profile={profile || null}
              />
            )}
          </div>
          <div className="flex-1">
            <FAQSection />
          </div>
        </div>
      )}
      
      {/* For active subscribers, show API Key, VM Instances, and Subscription sections */}
      {isSubscriptionActive && (
        <>
          {/* API Key Section */}
          <div>
            <ApiKeyManager />
          </div>
          
          {/* VM Instances Section */}
          <div>
            <VMInstancesManager />
          </div>
          
          {/* Subscription Management Section */}
          <div>
            <SubscriptionSection 
              userEmail={userEmail}
              userId={userId}
              profile={profile}
            />
          </div>
        </>
      )}
    </div>
  )
}
