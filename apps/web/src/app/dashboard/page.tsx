import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { stripe } from '@/utils/stripe-server';
import type { Profile } from '@/types/database';
import { DashboardLayout } from '@/components/dashboard/dashboard-layout';
import { DashboardContent } from './dashboard-content';
import { createClient } from '@/utils/supabase/server';

export default async function Dashboard() {
  const supabase = createClient();
  
  // Check if user is authenticated - using getUser() for better security
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) {
    redirect('/login');
  }
  
  const userId = user.id;
  
  // Query the profiles table for the user
  const { data: dbProfile, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single();

  let profile: Profile | null = dbProfile;
  
  if (error && error.code !== 'PGRST116') {
    // PGRST116 is the error code for "no rows returned" - we handle this case separately
    console.error('Error fetching profile:', error);
  }
  
  // If profile doesn't exist, create it along with a Stripe customer
  if (!profile) {
    try {
      // Create a Stripe customer
      const customer = await stripe.customers.create({
        email: user.email,
        metadata: {
          userId: userId
        }
      });
      
      // Create a profile entry with the Stripe customer ID
      const newProfile: Profile = {
        id: userId,
        stripe_customer_id: customer.id,
        subscription_status: 'inactive',
        created_at: new Date(),
        updated_at: new Date()
      };
      
      const { error: insertError } = await supabase
        .from('profiles')
        .insert(newProfile);

      profile = newProfile;
      
      if (insertError) {
        console.error('Error creating profile:', insertError);
      }
    } catch (err) {
      console.error('Error creating Stripe customer:', err);
    }
  }
  
  // Get session for client components
  const { data: { session } } = await supabase.auth.getSession();
  
  return (
    <DashboardLayout userEmail={user.email}>
      <DashboardContent 
        userEmail={user.email}
        userId={userId}
        profile={profile}
      />
    </DashboardLayout>
  );
}
