import OpenAI from 'openai';    
import Anthropic from '@anthropic-ai/sdk';

/**
 * Function to call OpenAI's computer-use-preview model
 * @param environment - The environment to use ('browser', 'mac', 'windows', 'ubuntu')
 * @param image_base64 - Optional base64-encoded screenshot
 * @param user_prompt - The user's prompt
 * @returns The response from the OpenAI API
 */
export async function callComputerUsePreview(environment: 'browser' | 'mac' | 'windows' | 'ubuntu', user_prompt: string, image_base64?: string) {
    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  
    // Prepare the input array
    const input: any[] = [
      {
        role: "user",
        content: user_prompt,
      }
    ];
  
    // Add screenshot if provided
    if (image_base64) {
      input.push({
        type: "input_image",
        image_url: `data:image/png;base64,${image_base64}`
      });
    }
  
    // Call the OpenAI API
    const response = await openai.responses.create({
      model: "computer-use-preview",
      tools: [
        {
          type: "computer-preview",
          display_width: 1024,
          display_height: 768,
          environment: environment,
        },
      ],
      input: input,
      reasoning: {
        generate_summary: "concise",
      },
      truncation: "auto",
    });
  
    return response;
  }

export async function claudeComputerUse() {
    const anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
    });

    const message = await anthropic.beta.messages.create({
        model: "claude-3-7-sonnet-20250219",
        max_tokens: 1024,
        tools: [
            {
              type: "computer_20250124",
              name: "computer",
              display_width_px: 1024,
              display_height_px: 768,
              display_number: 1
            },
            {
              type: "text_editor_20241022",
              name: "str_replace_editor"
            },
            {
              type: "bash_20241022",
              name: "bash"
            }
        ],
        messages: [{ role: "user", content: "Save a picture of a cat to my desktop." }],
        betas: ["computer-use-2025-01-24"],
        thinking: { type: "enabled", budget_tokens: 1024 }
      });

    return message;
}