'use client'

import { DemoSection } from '@/components/demo-section'
import { Thread } from '@/components/thread'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import {
  ChatBubbleLeftIcon,
  ComputerDesktopIcon,
  HeartIcon,
} from '@heroicons/react/24/outline'
import { useState } from 'react'

export default function PlaygroundDemo() {
  // State to store the desktop ID
  const [desktopId, setDesktopId] = useState<string | null>(null)
  // State to track if the demo has been finished
  const [finishedDemo, setFinishedDemo] = useState(false)

  // Update the chat runtime to support OpenAI Responses API features
  const runtime = useChatRuntime({
    api: '/api/chat',
    // Use headers instead of body to pass the desktopId
    headers: () => {
      // Use the actual desktopId from state, or a fallback value if it's null
      const currentDesktopId = desktopId || 'NO_DESKTOP_ID_YET'
      console.log(
        '[useChatRuntime] Sending request with desktopId in headers:',
        currentDesktopId,
      )

      return Promise.resolve({
        'Content-Type': 'application/json',
        'X-Desktop-Id': currentDesktopId,
      })
    },
    onFinish: (message) => {
      const sources = message.metadata?.custom?.sources
      if (sources) {
        console.log('Web search sources:', sources)
      }
    },
  })
  // Function to handle when a desktop is deployed
  const handleDesktopDeployed = (id: string) => {
    // Set the desktop ID directly from the API response
    setDesktopId(id)
  }

  const handleDesktopStopped = () => {
    // Set the desktop ID directly from the API response
    setDesktopId(null)
    // Set finishedDemo to true when desktop is stopped
    setFinishedDemo(true)
  }

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="mx-auto flex h-auto w-full max-w-7xl flex-col gap-4 px-2 md:flex-row">
        {/* Thread Area */}
        <div className="order-2 flex h-[400px] flex-col items-center md:order-1 md:h-[500px] md:w-1/4 md:flex-none">
          {desktopId ? (
            <div className="h-full w-full overflow-auto rounded-lg border border-gray-200 bg-gray-50">
              <Thread />
              {/* Add a button to stop the desktop on mobile and tablet only */}
            </div>
          ) : (
            <div className="flex h-full w-full items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-400">
              <div className="py-12 text-center">
                {finishedDemo ? (
                  <HeartIcon className="mx-auto mb-6 h-16 w-16 text-gray-300" />
                ) : (
                  <ChatBubbleLeftIcon className="mx-auto mb-6 h-16 w-16 text-gray-300" />
                )}
                <p className="max-w-md px-10 text-center text-base">
                  {finishedDemo
                    ? 'Thank you for trying our demo! Sign up to get started.'
                    : 'Launch the demo to start chatting with the assistant.'}
                </p>
              </div>
            </div>
          )}
          {/* The mobile stop button is now handled by a reference to the DemoSection component */}
        </div>
        

        {/* Demo Section */}
        <div className="order-1 flex-1 overflow-visible p-0.5 md:order-2 md:w-3/4 md:flex-none">
          <DemoSection
            onDesktopDeployed={handleDesktopDeployed}
            onDesktopStopped={handleDesktopStopped}
            hideIntro={true}
            desktopId={desktopId || undefined}
          />
        </div>
      </div>
    </AssistantRuntimeProvider>
  )
}
