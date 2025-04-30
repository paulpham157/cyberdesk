import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
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
  
  console.log('[API_ROUTE_PATCH] Attempting to parse request body...');
  const body = await request.json();
  const { id } = body;
  console.log('[API_ROUTE_PATCH] Parsed request body:', body);
  console.log('[API_ROUTE_PATCH] Received request');
  
  try {
    console.log('[API_ROUTE_PATCH] Attempting to parse request body...');
    const body = await request.json();
    const { id } = body;
    console.log('[API_ROUTE_PATCH] Parsed request body:', body);
    
    if (!id) {
      console.error('[API_ROUTE_PATCH] Desktop ID is required but not found in body');
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
    console.log('[API_ROUTE_PATCH] Client call successful. Returning success.');
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error stopping desktop:', error);
    return NextResponse.json(
      { error: 'Failed to stop desktop' },
      { status: 500 }
    );
  }

}
