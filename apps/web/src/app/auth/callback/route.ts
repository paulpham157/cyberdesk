import { createClient } from '@/utils/supabase/server'
import { NextRequest, NextResponse } from 'next/server'
import PostHogClient from '@/utils/posthog/posthog'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const error = requestUrl.searchParams.get('error')
  const errorDescription = requestUrl.searchParams.get('error_description')
  
  // Create a response that will be used for redirecting
  const redirectUrl = new URL('/dashboard', request.url)
  
  if (error) {
    console.error(`Auth error: ${error}, Description: ${errorDescription}`)
    // If there's an error, redirect to login
    redirectUrl.pathname = '/login'
    // Add error information as query parameters
    redirectUrl.searchParams.set('error', error)
    if (errorDescription) {
      redirectUrl.searchParams.set('error_description', errorDescription)
    }
  } else if (code) {
    try {
      const supabase = createClient()
      
      // Exchange the code for a session
      const { data } = await supabase.auth.exchangeCodeForSession(code)
      
      // Identify the user in PostHog
      if (data?.user) {
        const posthog = PostHogClient()
        // Use the correct identify method signature for posthog-node
        posthog.identify({
          distinctId: data.user.id,
          properties: {
            email: data.user.email,
            name: data.user.user_metadata?.full_name || data.user.user_metadata?.name
          }
        })
      }
    } catch (err) {
      console.error('Error exchanging code for session:', err)
      // If there's an error, redirect to login
      redirectUrl.pathname = '/login'
      redirectUrl.searchParams.set('error', 'session_exchange_error')
    }
  }
  
  // URL to redirect to after sign in process completes
  return NextResponse.redirect(redirectUrl)
}
