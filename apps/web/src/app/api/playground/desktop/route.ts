import { NextResponse } from 'next/server';
import client from '@/lib/cyberdeskClient';

/**
 * Deploy a virtual desktop for playground/demo purposes
 * This endpoint uses the Cyberdesk client
 */
export async function POST(request: Request) {
  console.log('[API_ROUTE_POST] Received request');
  try {
    console.log('[API_ROUTE_POST] Attempting to parse request body...');
    const body = await request.json();
    const { timeoutMs } = body;
    console.log('[API_ROUTE_POST] Parsed request body:', body);

    if (!timeoutMs) {
      console.warn('[API_ROUTE_POST] timeoutMs not found in request body');
      // You might want to return an error here if timeoutMs is required
    }

    console.log(`[API_ROUTE_POST] Calling client.postV1Desktop with timeoutMs: ${timeoutMs}`);
    const result = await client.launchDesktop({ body: { timeout_ms: timeoutMs } });
    console.log('[API_ROUTE_POST] Received result from client.postV1Desktop:', JSON.stringify(result, null, 2)); // Log the full result

    // Check status code from the nested response object
    if (result.response.status !== 200 && result.response.status !== 201) {
      console.log(`[API_ROUTE_POST] Client call failed with status: ${result.response.status}`);
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        console.log('[API_ROUTE_POST] Attempting to parse error response body...');
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
        console.log('[API_ROUTE_POST] Parsed error details:', errorDetails);
      } catch (e) { 
        console.log('[API_ROUTE_POST] Failed to parse error response body as JSON.', e);
      }
      console.error('[API_ROUTE_POST] Cyberdesk client failed to deploy desktop:', errorDetails);
      return NextResponse.json(
        { error: `Failed to deploy desktop: ${errorDetails}` },
        { status: result.response.status }
      );
    }

    console.log('[API_ROUTE_POST] Client call successful.');
    const data = result.data;
    const id = result.data?.id;
    
    if (!data) {
        console.error('[API_ROUTE_POST] No data received from successful deploy call');
        return NextResponse.json(
            { error: 'No data received from successful deploy call' },
            { status: 500 }
        );
    }

    console.log('[API_ROUTE_POST] Returning success response with data:', data);
    return NextResponse.json({ 
      id: data.id,
      status: data.status
    });

  } catch (error: any) { // Type error as any for broader catch
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
    console.error('[API_ROUTE_POST] EXCEPTION CAUGHT IN POST HANDLER:', error);
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
    
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
  console.log('[API_ROUTE_PATCH] Received request');
  try {
    console.log('[API_ROUTE_PATCH] Attempting to parse request body...');
    const body = await request.json();
    const { id } = body;
    console.log('[API_ROUTE_PATCH] Parsed request body:', body);
    
    if (!id) {
      console.error('[API_ROUTE_PATCH] Desktop ID is required but not found in body');
      return NextResponse.json(
        { error: 'Desktop ID is required' },
        { status: 400 }
      );
    }
    
    console.log(`[API_ROUTE_PATCH] Calling client.postV1DesktopIdStop with id: ${id}`);
    const result = await client.terminateDesktop({ path: { id } });
    console.log('[API_ROUTE_PATCH] Received result from client.postV1DesktopIdStop:', JSON.stringify(result, null, 2)); // Log the full result

    // Check status code from the nested response object
    if (result.response.status !== 200 && result.response.status !== 204) { // 204 No Content is also common for stops
      console.log(`[API_ROUTE_PATCH] Client call failed with status: ${result.response.status}`);
      let errorDetails = `Failed with status: ${result.response.status}`;
       try {
        console.log('[API_ROUTE_PATCH] Attempting to parse error response body...');
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
        console.log('[API_ROUTE_PATCH] Parsed error details:', errorDetails);
      } catch (e) {
        console.log('[API_ROUTE_PATCH] Failed to parse error response body as JSON.', e);
      }
      console.error('[API_ROUTE_PATCH] Cyberdesk client failed to stop desktop:', errorDetails);
      return NextResponse.json(
        { error: `Failed to stop desktop: ${errorDetails}` },
        { status: result.response.status }
      );
    }
    
    console.log('[API_ROUTE_PATCH] Client call successful. Returning success.');
    return NextResponse.json({ success: true });

  } catch (error: any) { // Type error as any for broader catch
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
    console.error('[API_ROUTE_PATCH] EXCEPTION CAUGHT IN PATCH HANDLER:', error);
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');

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
  console.log('[API_ROUTE_GET] Received request');
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');
  console.log(`[API_ROUTE_GET] Extracted id: ${id}`);

  if (!id) {
    console.error('[API_ROUTE_GET] Desktop ID is required but not found in query parameters');
    return NextResponse.json(
      { error: 'Desktop ID is required in query parameters' },
      { status: 400 }
    );
  }

  try {
    // Add trimming and type check
    const trimmedId = id?.trim();
    if (!trimmedId) {
        console.error('[API_ROUTE_GET] ID is missing or empty after trimming.');
        return NextResponse.json(
            { error: 'Desktop ID is required and cannot be empty' },
            { status: 400 }
        );
    }
    // Optional: Add a basic regex check for UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(trimmedId)) {
         console.error(`[API_ROUTE_GET] Invalid UUID format detected before SDK call: ${trimmedId}`);
         return NextResponse.json(
            { error: `Invalid Desktop ID format: ${trimmedId}` },
            { status: 400 }
         );
    }

    console.log(`[API_ROUTE_GET] Calling client.getDesktopInfo with id: ${id}`);
    const result = await client.getDesktopInfo({ path: { id } });
    console.log('[API_ROUTE_GET] Received result from client.getDesktopInfo:', JSON.stringify(result, null, 2));

    // Check status code from the nested response object
    if (result.response.status !== 200) {
      console.log(`[API_ROUTE_GET] Client call failed with status: ${result.response.status}`);
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json();
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
        console.log('[API_ROUTE_GET] Parsed error details:', errorDetails);
      } catch (e) {
        console.log('[API_ROUTE_GET] Failed to parse error response body as JSON. Attempting to read as text...', e);
        try {
            // Clone the response before reading text, as body can only be read once
            const errorText = await result.response.clone().text(); 
            console.log('[API_ROUTE_GET] Error response body as text:', errorText);
            errorDetails = errorText || errorDetails; // Use text if available
        } catch (textError) {
            console.log('[API_ROUTE_GET] Failed to read error response body as text.', textError);
        }
      }
      console.error('[API_ROUTE_GET] Cyberdesk client failed to get desktop info:', errorDetails);
      // Return specific error format as requested
      return NextResponse.json(
        { status: 'error', stream_url: '' }, 
        { status: result.response.status } // Use original error status code
      );
    }

    console.log('[API_ROUTE_GET] Client call successful.');
    const data = result.data;

    if (!data) {
      console.error('[API_ROUTE_GET] No data received from successful get info call');
      // Return specific error format as requested
      return NextResponse.json(
        { status: 'error', stream_url: '' }, 
        { status: 500 }
      );
    }
    
    console.log('[API_ROUTE_GET] Returning success response with status and stream_url:', { status: data.status, stream_url: data.stream_url });
    return NextResponse.json({ 
      status: data.status, 
      stream_url: data.stream_url 
    });

  } catch (error: any) { // Type error as any for broader catch
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
    console.error('[API_ROUTE_GET] EXCEPTION CAUGHT IN GET HANDLER:', error);
    console.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');

    const status = error?.response?.status || 500;

    // Return specific error format as requested
    return NextResponse.json(
      { status: 'error', stream_url: '' }, 
      { status: status }
    );
  }
}
