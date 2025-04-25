"use client";
import { Button } from '@/components/button';
import { useState } from 'react';

interface SubscriptionManagementProps {
  customerId: string;
  className?: string;
}

export function SubscriptionManagement({
  customerId,
  className,
}: SubscriptionManagementProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleManageSubscription = async () => {
    try {
      setIsLoading(true);
      
      const response = await fetch('/api/stripe/portal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customerId,
          returnUrl: `${window.location.origin}/dashboard`,
        }),
      });

      const { url } = await response.json();
      
      if (url) {
        window.location.href = url;
      } else {
        throw new Error('Failed to create portal session');
      }
    } catch (error) {
      console.error('Error opening customer portal:', error);
      alert('Something went wrong. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={className}>
      <Button
        onClick={handleManageSubscription}
        disabled={isLoading}
        variant="outline"
      >
        {isLoading ? 'Loading...' : 'Manage Subscription'}
      </Button>
    </div>
  );
}
