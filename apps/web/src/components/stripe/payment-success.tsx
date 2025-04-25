import { Button } from '@/components/button';
import { Link } from '@/components/link';
import { CheckIcon } from '@heroicons/react/24/outline';

interface PaymentSuccessProps {
  className?: string;
}

export function PaymentSuccess({ className }: PaymentSuccessProps) {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-8 ${className}`}>
      <div className="rounded-full bg-green-100 p-3 mb-4">
        <CheckIcon className="h-8 w-8 text-green-600" />
      </div>
      
      <h2 className="text-2xl font-bold mb-2">Payment Successful!</h2>
      
      <p className="text-gray-600 mb-6 max-w-md">
        Thank you for your subscription. Your account has been upgraded and you now have access to all features.
      </p>
      
      <div className="flex gap-4">
        <Button href="/dashboard">
          Go to Dashboard
        </Button>
        
        <Button as="a" href="mailto:support@example.com" variant="outline">
          Need Help?
        </Button>
      </div>
    </div>
  );
}
