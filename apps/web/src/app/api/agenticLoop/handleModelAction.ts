// Define the types for different action types
export type ClickAction = {
  type: 'click';
  x: number;
  y: number;
  button?: 'left' | 'middle' | 'right';
};

export type ScrollAction = {
  type: 'scroll';
  x: number;
  y: number;
  scrollX?: number;
  scrollY?: number;
};

export type KeypressAction = {
  type: 'keypress';
  keys: string[];
};

export type TypeAction = {
  type: 'type';
  text: string;
};

export type WaitAction = {
  type: 'wait';
};

export type ScreenshotAction = {
  type: 'screenshot';
};

// Union type for all possible actions
export type ModelAction = 
  | ClickAction
  | ScrollAction
  | KeypressAction
  | TypeAction
  | WaitAction
  | ScreenshotAction;

// Type for button mapping
export type ButtonMap = {
  [key in 'left' | 'middle' | 'right']: number;
};

export async function handleModelAction(vm: string, action: ModelAction) {
    const actionType = action.type;
    const apiKey = process.env.CYBERDESK_API_KEY;
    
    if (!apiKey) {
      throw new Error("Missing API key");
    }
    
    try {
      const endpoint = `https://api.cyberdesk.io/v1/desktop/${vm}/computer-action`;
      const headers = {
        "x-api-key": apiKey,
        "Content-Type": "application/json"
      };
  
      switch (actionType) {
        case "click": {
          const { x, y, button = "left" } = action;
          const buttonMap: ButtonMap = { left: 1, middle: 2, right: 3 };
          const b = buttonMap[button] || 1;
  
          console.log(`Action: click at (${x}, ${y}) with button '${button}' mapped to ${b}`);
          await fetch(endpoint, {
            method: "POST",
            headers,
            body: JSON.stringify({
              type: `${b}_click`,
              x,
              y,
            })
          });
          break;
        }
  
        case "scroll": {
            const { x, y, scrollY = 0 } = action;
          
            console.log(`Action: move mouse to (${x}, ${y})`);
            await fetch(endpoint, {
              method: "POST",
              headers,
              body: JSON.stringify({
                type: "move",
                x,
                y
              })
            });
          
            if (scrollY > 0) {
              console.log(`Action: scroll up by ${scrollY}`);
              await fetch(endpoint, {
                method: "POST",
                headers,
                body: JSON.stringify({
                  type: "scroll",
                  direction: "up",
                  y: scrollY
                })
              });
            } else if (scrollY < 0) {
              console.log(`Action: scroll down by ${Math.abs(scrollY)}`);
              await fetch(endpoint, {
                method: "POST",
                headers,
                body: JSON.stringify({
                  type: "scroll",
                  direction: "down",
                  y: Math.abs(scrollY)
                })
              });
            }
            break;
          }
  
        case "keypress": {
          const { keys } = action;
          for (const k of keys) {
            console.log(`Action: keypress '${k}'`);
            await fetch(endpoint, {
              method: "POST",
              headers,
              body: JSON.stringify({
                type: "press",
                keys: k
              })
            });
          }
          break;
        }
  
        case "type": {
          const { text } = action;
          console.log(`Action: type text '${text}'`);
          await fetch(endpoint, {
            method: "POST",
            headers,
            body: JSON.stringify({
              type: "write",
              text
            })
          });
          break;
        }
  
        case "wait": {
          console.log(`Action: wait`);
          await new Promise((resolve) => setTimeout(resolve, 2000));
          break;
        }
  
        case "screenshot": {
          console.log(`Action: screenshot`);
          break;
        }
  
        default:
          console.log("Unrecognized action:", action);
      }
    } catch (e) {
      console.error("Error handling action", action, ":", e);
    }
  }