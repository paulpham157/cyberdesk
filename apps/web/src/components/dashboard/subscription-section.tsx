'use client'

import type { Profile } from '@/types/database'
import { SubscriptionManagement } from '@/components/stripe/subscription-management'
import { PricingCard } from '@/components/stripe/client-pricing-card'
import { tiers } from '@/utils/stripe/tiers'
import type { User } from '@supabase/supabase-js'

interface SubscriptionSectionProps {
  userEmail?: string;
  userId?: string;
  profile?: Profile | null;
}

export function SubscriptionSection({ userEmail, userId, profile }: SubscriptionSectionProps) {
  return (
    <div className="space-y-4">
      {/* Centered subscription content */}
      <div className="max-w-md mx-auto">
        <div className="bg-white border border-gray-200 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex items-center justify-center">
            <div className="flex items-center space-x-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              <h3 className="text-base font-medium text-gray-900">Subscription Status</h3>
            </div>
          </div>
          
          <div className="px-6 py-5">
            {!profile?.subscription_status || profile?.subscription_status === 'inactive' ? (
              <div className="p-0">
                <PricingCard 
                  tier={tiers[0]} 
                  user={userId ? { id: userId, email: userEmail } as User : null}
                  profile={profile || null}
                />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-50 rounded-md p-3">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">Subscription Active</h3>
                      <div className="mt-2 text-sm text-green-700">
                        <p>Status: <span className="font-medium">{profile.subscription_status}</span></p>
                        {profile.current_period_end && (
                          <p className="mt-1">Current period ends: <span className="font-medium">{new Date(profile.current_period_end).toLocaleDateString()}</span></p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-center">
                  {profile?.stripe_customer_id && (
                    <SubscriptionManagement 
                      customerId={profile.stripe_customer_id} 
                      className="w-full flex flex-col items-center"
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
