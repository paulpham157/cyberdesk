import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import client from '@/lib/cyberdeskClient';
/**
  * Deploy a virtual desktop for playground/demo purposes
  * This endpoint uses the Cyberdesk client
  */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { timeoutMs } = body;

    if (!timeoutMs) {
      // You might want to return an error here if timeoutMs is required
      console.warn('[API_ROUTE_POST] timeoutMs not found in request body');
    }

    const result = await client.launchDesktop({ body: { timeout_ms: timeoutMs } });

    if (result.response.status !== 200 && result.response.status !== 201) {
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) { 
        // Ignore parsing error
      }
      console.error('[API_ROUTE_POST] Cyberdesk client failed to deploy desktop:', errorDetails);
      return NextResponse.json(
        { error: `Failed to deploy desktop: ${errorDetails}` },
        { status: result.response.status }
      );
    }

    const data = result.data;
    if (!data) {
        console.error('[API_ROUTE_POST] No data received from successful deploy call');
        return NextResponse.json(
            { error: 'No data received from successful deploy call' },
            { status: 500 }
        );
    }

    return NextResponse.json({ 
      id: data.id,
      status: data.status
    });

  } catch (error: any) {
    console.error('[API_ROUTE_POST] EXCEPTION CAUGHT IN POST HANDLER:', error);
    const status = error?.response?.status || 500;
    const message = error?.message || 'Internal server error deploying desktop';
    return NextResponse.json(
      { error: message },
      { status: status }
    );
  }
}
 

/**
  * Stop a virtual desktop
  * This endpoint uses the Cyberdesk client
  */
export async function PATCH(request: Request) {
  try {
    const body = await request.json();
    const { id } = body;

    if (!id) {
      console.error('[API_ROUTE_PATCH] Desktop ID is required but not found in body');
      return NextResponse.json(
        { error: 'Desktop ID is required' },
        { status: 400 }
      );
    }

    const result = await client.terminateDesktop({ path: { id } });

    if (result.response.status !== 200 && result.response.status !== 204) {
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) {
        // Ignore parsing error
      }
      console.error('[API_ROUTE_PATCH] Cyberdesk client failed to stop desktop:', errorDetails);
      return NextResponse.json(
        { error: `Failed to stop desktop: ${errorDetails}` },
        { status: result.response.status }
      );
    }

    return NextResponse.json({ success: true });

  } catch (error: any) {
    console.error('[API_ROUTE_PATCH] EXCEPTION CAUGHT IN PATCH HANDLER:', error);
    const status = error?.response?.status || 500;
    const message = error?.message || 'Internal server error stopping desktop';
    return NextResponse.json(
      { error: message },
      { status: status }
    );
  }
}



/**
  * Get desktop status and stream URL
  * This endpoint uses the Cyberdesk client
  */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    console.error('[API_ROUTE_GET] Desktop ID is required but not found in query parameters');
    return NextResponse.json(
      { error: 'Desktop ID is required in query parameters' },
      { status: 400 }
    );
  }

  try {
    const trimmedId = id?.trim();
    if (!trimmedId) {
        console.error('[API_ROUTE_GET] ID is missing or empty after trimming.');
        return NextResponse.json(
            { error: 'Desktop ID is required and cannot be empty' },
            { status: 400 }
        );
    }
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(trimmedId)) {
         console.error(`[API_ROUTE_GET] Invalid UUID format detected before SDK call: ${trimmedId}`);
         return NextResponse.json(
            { error: `Invalid Desktop ID format: ${trimmedId}` },
            { status: 400 }
         );
    }

    const result = await client.getDesktop({ path: { id } });

    if (result.response.status !== 200) {
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json();
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) {
        try {
            const errorText = await result.response.clone().text(); 
            errorDetails = errorText || errorDetails;
        } catch (textError) {
            // Ignore parsing error
        }
      }
      console.error('[API_ROUTE_GET] Cyberdesk client failed to get desktop info:', errorDetails);
      return NextResponse.json(
        { status: 'error', stream_url: '' }, 
        { status: result.response.status }
      );
    }

    const data = result.data;
    if (!data) {
      console.error('[API_ROUTE_GET] No data received from successful get info call');
      return NextResponse.json(
        { status: 'error', stream_url: '' }, 
        { status: 500 }
      );
    }

    return NextResponse.json({ 
      status: data.status, 
      stream_url: data.stream_url 
    });

  } catch (error: any) {
    console.error('[API_ROUTE_GET] EXCEPTION CAUGHT IN GET HANDLER:', error);
    const status = error?.response?.status || 500;
    return NextResponse.json(
      { status: 'error', stream_url: '' }, 
      { status: status }
    );
  }
}