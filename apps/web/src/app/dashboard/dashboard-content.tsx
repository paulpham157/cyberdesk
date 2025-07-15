'use client'

import { SubscriptionSection } from '@/components/dashboard/subscription-section'
import type { Profile } from '@/types/database'
import { ApiKeyManager } from '@/components/dashboard/api-key-manager'
import { VMInstancesManager } from '@/components/dashboard/vm-instances-manager'
import { supabase } from '@/utils/supabase/client'
import { ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/button'
import posthog from 'posthog-js'
// import { Subheading } from '@/components/text'

interface DashboardContentProps {
  userEmail?: string;
  userId?: string;
  profile?: Profile | null;
}

export function DashboardContent({ userEmail, userId, profile }: DashboardContentProps) {
  const isSubscriptionActive = profile?.subscription_status === "active";
  // Removed fetching active subscriptions as pricing card is no longer displayed for non-subscribers
  
  // Removed fetching active subscriptions as pricing card is no longer displayed for non-subscribers
  
  const handleLogout = async () => {
    // Reset PostHog user to anonymous before logging out
    posthog.reset();
    
    await supabase.auth.signOut();
    window.location.href = '/';
  };
  
  // const isSoldOut = activeSubscriptionsCount !== null && activeSubscriptionsCount >= SUBSCRIPTION_LIMIT;

  // If subscription is not active, show booking message instead of pricing/FAQ
  if (!isSubscriptionActive) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center space-y-6">
        <h2 className="text-3xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
          Looks like we haven&apos;t set up your account yet.
        </h2>
        <p className="max-w-lg text-base/7 text-gray-600">
          Book a time here to get you up and running soon!
        </p>
        <Button href="https://cal.com/mahmoud-al-madi-klrs5s/30min" target="_blank" rel="noopener noreferrer">
          Book a demo
        </Button>
      </div>
    );
  }
  
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
      
      {/* Pricing and FAQ sections have been removed for non-subscribers */}
      
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
