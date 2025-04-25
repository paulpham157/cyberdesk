import OpenAI from "openai";
import takeScreenshot from "./takeScreenshot";
import { handleModelAction } from "./handleModelAction";
const openai = new OpenAI();

export async function computerUseLoop(instance: string, response: any) {
  /**
   * Run the loop that executes computer actions until no 'computer_call' is found.
   */
  while (true) {
    const computerCalls = response.output.filter(
      (item: { type: string; }) => item.type === "computer_call"
    );
    if (computerCalls.length === 0) {
      console.log("No computer call found. Output from model:");
      response.output.forEach((item: any) => {
        console.log(JSON.stringify(item, null, 2));
      });
      break; // Exit when no computer calls are issued.
    }

    // We expect at most one computer call per response.
    const computerCall = computerCalls[0];
    const lastCallId = computerCall.call_id;
    const action = computerCall.action;

    // Execute the action (function defined in step 3)
    handleModelAction(instance, action);
    await new Promise((resolve) => setTimeout(resolve, 2000)); // Allow time for changes to take effect.

    const screenshotBase64 = await takeScreenshot(instance);

    // Send the screenshot back as a computer_call_output
    response = await openai.responses.create({
      model: "computer-use-preview",
      previous_response_id: response.id,
      tools: [
        {
          type: "computer-preview",
          display_width: 1024,
          display_height: 768,
          environment: "browser",
        },
      ],
      input: [
        {
          call_id: lastCallId,
          type: "computer_call_output",
          output: {
            type: "computer_screenshot",
            image_url: `data:image/png;base64,${screenshotBase64}`,
          },
        },
      ],
      truncation: "auto",
    });
  }

  return response;
}