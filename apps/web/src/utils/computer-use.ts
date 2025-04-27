/**
 * Utility functions for computer control with Cyberdesk API
 */

import client from '@/lib/cyberdeskClient';

/**
 * Get the base API URL based on environment
 */


/**
 * Get a screenshot of the current display
 * @param desktopId The ID of the desktop instance
 * @returns Base64 encoded PNG image data
 */
export async function getScreenshot(desktopId: string): Promise<string> {
  try {
    const result = await client.executeActionOnDesktop({
        path: { id: desktopId },
        body: { type: 'screenshot' },
    } as any);

    if (result.response.status !== 200) {
      let errorDetails = `Failed with status: ${result.response.status}`;
      try {
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) { /* Failed to parse body */ }
      throw new Error(`Failed to get screenshot: ${errorDetails}`);
    }

    const data = result.data;
    return data?.base64_image || ''; 
  } catch (error) {
    console.error('Error getting screenshot:', error);
    throw error;
  }
}

/**
 * Execute a computer action based on the provided parameters
 * @param action The action to perform (click, type, etc.)
 * @param desktopId The ID of the desktop instance
 * @param coordinate The coordinates for actions that require a position
 * @param text The text for actions that require text input
 * @param duration The duration for wait actions (in seconds, converted to ms)
 * @param scroll_amount The number of clicks to scroll
 * @param scroll_direction The direction to scroll (up or down)
 * @param start_coordinate The starting coordinates for drag actions
 * @returns Result of the action, either a string or an object with image data
 */
export async function executeComputerAction(
  action: string,
  desktopId: string,
  coordinate?: { x: number; y: number }, 
  text?: string,
  duration?: number,
  scroll_amount?: number,
  scroll_direction?: 'up' | 'down',
  start_coordinate?: { x: number; y: number }
): Promise<string | { type: "image"; data: string }> {
  try {
    let requestBody: any = {};

    // Map the action to the API's expected format
    switch (action) {
      case 'left_click':
        requestBody = {
          type: 'click_mouse',
          x: coordinate?.x,
          y: coordinate?.y,
          button: 'left',
          click_type: 'click',
          num_of_clicks: 1
        };
        break;
        
      case 'right_click':
        requestBody = {
          type: 'click_mouse',
          x: coordinate?.x,
          y: coordinate?.y,
          button: 'right',
          click_type: 'click',
          num_of_clicks: 1
        };
        break;
        
      case 'middle_click':
        requestBody = {
          type: 'click_mouse',
          x: coordinate?.x,
          y: coordinate?.y,
          button: 'middle',
          click_type: 'click',
          num_of_clicks: 1
        };
        break;
        
      case 'double_click':
         requestBody = {
          type: 'click_mouse',
          x: coordinate?.x,
          y: coordinate?.y,
          button: 'left',
          click_type: 'click',
          num_of_clicks: 2
        };
        break;
        
      case 'mouse_move':
        requestBody = {
          type: 'move_mouse',
          x: coordinate?.x || 0,
          y: coordinate?.y || 0
        };
        break;
        
      case 'left_mouse_down':
        requestBody = {
          type: 'click_mouse',
          button: 'left',
          click_type: 'down'
        };
        break;
        
      case 'left_mouse_up':
        requestBody = {
          type: 'click_mouse',
          button: 'left',
          click_type: 'up'
        };
        break;
        
      case 'scroll':
        requestBody = {
          type: 'scroll',
          direction: scroll_direction || 'down',
          amount: scroll_amount || 1
        };
        break;
        
      case 'type':
        requestBody = {
          type: 'type',
          text: text || ''
        };
        break;
        
      case 'key':
        requestBody = {
          type: 'press_keys',
          keys: text || '',
          key_action_type: 'press'
        };
        break;
        
      case 'left_click_drag':
        if (start_coordinate && coordinate) {
          requestBody = {
            type: 'drag_mouse',
            start: {
              x: start_coordinate.x,
              y: start_coordinate.y
            },
            end: {
              x: coordinate.x,
              y: coordinate.y
            }
          };
        } else {
          throw new Error("Start and end coordinates are required for drag action.");
        }
        break;
        
      case 'wait':
        requestBody = {
          type: 'wait',
          ms: (duration || 1) * 1000
        };
        break;
        
      }    

    // Construct the parameters for the client call
    const clientParams: any = {
        path: { id: desktopId },
        body: requestBody as any
    };

    const result = await client.executeActionOnDesktop(clientParams);

    if (result.response.status !== 200) {
      let errorDetails = `Failed with status: ${result.response.status}`;
       try {
        const errorBody = await result.response.json(); 
        errorDetails = errorBody.message || errorBody.error || JSON.stringify(errorBody);
      } catch (e) { /* Failed to parse body */ }
      throw new Error(`Failed to execute computer action ${action}: ${errorDetails}`);
    }

    const data = result.data;
    
    // Check for image data in the response
    if (data?.base64_image) { 
      return {
        type: "image",
        data: data.base64_image
      };
    }
    
    // Return status or a default success message
    return data?.output || 'Action completed successfully'; 
  } catch (error) {
    console.error(`Error executing computer action ${action}:`, error);
    throw error;
  }
}
