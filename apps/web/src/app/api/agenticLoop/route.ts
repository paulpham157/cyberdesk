import { NextResponse } from 'next/server';
import OpenAI from 'openai';
import takeScreenshot from './takeScreenshot';
import { callComputerUsePreview } from './computerUsePreview';
import { computerUseLoop } from './computerUseLoop';

/**
 * Execute the agentic loop with OpenAI and Cyberdesk
 * This endpoint takes an instanceId and prompt, then executes
 * the agentic loop as described in the OpenAI documentation
 */
export async function POST(request: Request) {
  try {
    // Get API keys from environment variables
    const CYBERDESK_API_KEY = process.env.CYBERDESK_API_KEY;
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
    
    if (!CYBERDESK_API_KEY || !OPENAI_API_KEY) {
      console.error('Missing API keys');
      return NextResponse.json(
        { error: 'Server configuration error: Missing API keys' },
        { status: 500 }
      );
    }
    
    // Get the instanceId and prompt from the request body
    const { instanceId, prompt } = await request.json();
    
    if (!instanceId || !prompt) {
      return NextResponse.json(
        { error: 'Missing required parameters: instanceId and prompt' },
        { status: 400 }
      );
    }
    
    // Start the conversation with the user's prompt
    const image = await takeScreenshot(instanceId);

    console.log('Screenshot taken:', image)
    console.log('Gonna query openai')
    // Call OpenAI's computer-use-preview model
    const initialResponse = await callComputerUsePreview('ubuntu', prompt, image);
    console.log('open ai response', initialResponse)
    console.log('Gonna query computer loopp')
    const finalResponse = await computerUseLoop(instanceId, initialResponse);    

    // Return the final response
    return NextResponse.json({ response: finalResponse });
    
  } catch (error) {
    console.error('Error in agentic loop:', error);
    return NextResponse.json(
      { 
        error: 'Failed to execute agentic loop', 
        details: error instanceof Error ? error.message : String(error) 
      },
      { status: 500 }
    );
  }
}
