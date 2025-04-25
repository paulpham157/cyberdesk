import { NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';

// Unkey API endpoints
const UNKEY_API_URL = 'https://api.unkey.dev/v1';
const UNKEY_API_ID = process.env.UNKEY_API_ID;
const UNKEY_ROOT_KEY = process.env.UNKEY_ROOT_KEY;

// Force dynamic rendering to ensure fresh data
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET(request: Request) {
  console.log('API route called');
  
  // Get userId from query parameters
  const url = new URL(request.url);
  const userId = url.searchParams.get('userId');
  console.log('Received userId from query:', userId);
  
  if (!userId) {
    return NextResponse.json({ error: 'UserId is required' }, { status: 400 });
  }
  
  // Create Supabase client
  const supabase = createClient();
  
  try {
    // Check if user exists in profiles table
    const { data: profileData, error: profileError } = await supabase
      .from('profiles')
      .select('id, unkey_key_id')
      .eq('id', userId)
      .single();
    
    console.log('Profile data:', profileData);
    
    if (profileError && profileError.code !== 'PGRST116') { // PGRST116 is the error code for 'no rows returned'
      console.error('Error fetching profile:', profileError);
      return NextResponse.json({ error: 'Failed to fetch user profile' }, { status: 500 });
    }
    
    // If user doesn't exist in profiles, create an entry
    if (!profileData) {
      console.log('Creating new profile for user:', userId);
      const { error: insertError } = await supabase
        .from('profiles')
        .insert({ id: userId });
      
      if (insertError) {
        console.error('Error creating profile:', insertError);
        return NextResponse.json({ error: 'Failed to create user profile' }, { status: 500 });
      }
      
      // Return that API key doesn't exist
      return NextResponse.json({ exists: false });
    }
    
    // Only return exists: true if the user has a non-null unkey_key_id
    if (!profileData.unkey_key_id) {
      console.log('User exists but has no API key');
      return NextResponse.json({ exists: false });
    }
    
    // At this point, we have a user with a non-null unkey_key_id
    console.log('User has an API key ID:', profileData.unkey_key_id);
    
    // Check if the key exists in Unkey
    const getKeyResponse = await fetch(
      `${UNKEY_API_URL}/keys.getKey?keyId=${profileData.unkey_key_id}`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${UNKEY_ROOT_KEY}`,
        },
      }
    );
    
    // If key doesn't exist in Unkey, return that it doesn't exist
    if (!getKeyResponse.ok) {
      console.log('Key ID exists in profile but not in Unkey');
      return NextResponse.json({ exists: false });
    }
    
    const keyData = await getKeyResponse.json();
    console.log('Key found in Unkey');
    
    return NextResponse.json({ 
      exists: true,
      key: keyData.key
    });
  } catch (error) {
    console.error('Error checking API key:', error);
    return NextResponse.json({ error: 'Failed to check API key' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  // Parse the request body to get the userId
  let userId;
  try {
    const body = await request.json();
    userId = body.userId;
    console.log('Received userId for key creation:', userId);
    
    if (!userId) {
      return NextResponse.json({ error: 'UserId is required' }, { status: 400 });
    }
  } catch (error) {
    console.error('Error parsing request body:', error);
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
  
  // Create Supabase client
  const supabase = createClient();
  
  try {
    // Check if user exists in profiles table
    const { data: profileData, error: profileError } = await supabase
      .from('profiles')
      .select('id, unkey_key_id')
      .eq('id', userId)
      .single();
    
    if (profileError && profileError.code !== 'PGRST116') {
      console.error('Error fetching profile:', profileError);
      return NextResponse.json({ error: 'Failed to fetch user profile' }, { status: 500 });
    }

  
    // Create an API key for the user
    const createKeyResponse = await fetch(`${UNKEY_API_URL}/keys.createKey`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${UNKEY_ROOT_KEY}`,
      },
      body: JSON.stringify({
        apiId: UNKEY_API_ID,
        prefix: 'cd',
        byteLength: 16,
        externalId: userId,
        meta: {
          createdAt: new Date().toISOString(),
          userId
        },
      }),
    });

    if (!createKeyResponse.ok) {
      const errorText = await createKeyResponse.text();
      console.log('Error creating key:', errorText);
      throw new Error(`Failed to create key: ${createKeyResponse.statusText}`);
    }

    const keyData = await createKeyResponse.json();
    console.log('Key created:', keyData.keyId);
    
    // Update the user's profile with the key ID
    const { error: updateError } = await supabase
      .from('profiles')
      .update({ unkey_key_id: keyData.keyId })
      .eq('id', userId);
    
    if (updateError) {
      console.error('Error updating profile with key ID:', updateError);
      // We'll still return the key even if updating the profile fails
    }

    return NextResponse.json({ 
      success: true, 
      key: keyData.key,
      keyId: keyData.keyId,
    });
  } catch (error) {
    console.error('Error creating API key:', error);
    return NextResponse.json({ error: 'Failed to create API key' }, { status: 500 });
  }
}
