/**
 * Utility functions for computer control with Cyberdesk API
 */

import client from '@/lib/cyberdeskClient';
import type { ExecuteComputerActionParams } from "cyberdesk"

/**
 * Get the base API URL based on environment
 */

// Define a named union type for all possible actions
export type ClaudeComputerActionType0124 =
  | "left_click"
  | "right_click"
  | "middle_click"
  | "double_click"
  | "triple_click"
  | "mouse_move"
  | "left_mouse_down"
  | "left_mouse_up"
  | "scroll"
  | "type"
  | "key"
  | "hold_key"
  | "cursor_position"
  | "left_click_drag"
  | "wait"
  | "screenshot";

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
  action: ClaudeComputerActionType0124,
  desktopId: string,
  coordinate?: { x: number; y: number },
  text?: string,
  duration?: number,
  scroll_amount?: number,
  scroll_direction?: "left" | "right" | "down" | "up",
  start_coordinate?: { x: number; y: number }
): Promise<string | { type: "image"; data: string }> {
  try {
    let requestBody: ExecuteComputerActionParams['body'];

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

      case 'triple_click':
        requestBody = {
          type: 'click_mouse',
          x: coordinate?.x,
          y: coordinate?.y,
          button: 'left',
          click_type: 'click',
          num_of_clicks: 3
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

      case 'hold_key':
        console.log(`Unhandled action: hold_key`);
        return "Hold key action support coming soon!"

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

      case 'screenshot':
        requestBody = {
          type: 'screenshot'
        };
        break;

      case 'cursor_position':
        requestBody = {
          type: 'get_cursor_position'
        };
        break;

      // EXHAUSTIVENESS CHECK:
      default: {
        const _exhaustiveCheck: never = action;
        throw new Error(`Unhandled action: ${action}`);
      }
    }

    // Construct the parameters for the client call
    const clientParams: ExecuteComputerActionParams = {
      path: { id: desktopId },
      body: requestBody
    };

    const result = await client.executeComputerAction(clientParams);

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
