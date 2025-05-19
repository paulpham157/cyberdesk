'use client'

import { Button } from '@/components/button'
import { supabase } from '@/utils/supabase/client'
import { ComputerDesktopIcon } from '@heroicons/react/24/outline'
import { ChevronRightIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/solid'
import React, { useEffect, useState, useRef, useCallback, forwardRef } from 'react'

const DESKTOP_TIMEOUT_MS = 600000

// Types
interface DemoSectionProps {
  onDesktopDeployed: (id: string) => void
  onDesktopStopped: () => void
  hideIntro?: boolean
  desktopId?: string
}

interface DesktopLaunchResponse {
  id: string
  status: string
}

// Main component
export function DemoSection({
  onDesktopDeployed,
  onDesktopStopped,
  hideIntro = false,
  desktopId,
}: DemoSectionProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [streamUrl, setStreamUrl] = useState<string>("")
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [isDemoLaunched, setIsDemoLaunched] = useState(false)
  const [hasEverLaunchedDemo, setHasEverLaunchedDemo] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const demoContentRef = useRef<HTMLDivElement>(null)

  // Check if user is logged in
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const { data } = await supabase.auth.getSession()
        setIsLoggedIn(!!data.session)
      } catch (error) {
        console.error('Error checking auth status:', error)
      } finally {
        setAuthLoading(false)
      }
    }
    checkAuthStatus()
  }, [])

  // Function to launch the demo
  const launchDemo = async () => {
    setIsLoading(true)
    setIsDemoLaunched(true)
    setHasEverLaunchedDemo(true)
    setError(null)
    setStreamUrl("")

    // Scroll to the demo content
    const isMobile = window.innerWidth < 768
    if (demoContentRef.current) {
      if (isMobile) {
        demoContentRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        demoContentRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }

    try {
      const { status, id } = await deployVirtualDesktop()
      if (!id || status === 'error') {
        setIsLoading(false)
        setError('Failed to deploy virtual desktop.')
        setIsDemoLaunched(false)
        return
      }
      if (onDesktopDeployed) onDesktopDeployed(id)

      // Poll for status
      let running = false
      let delay = 500 // Start with 0.5s
      let firstPoll = true
      while (!running) {
        try {
          const data = await getDetailsVirtualDesktop(id)
          if (data.status === 'running') {
            setStreamUrl(data.stream_url || "")
            running = true
            setIsLoading(false)
            break
          } else if (data.status === 'error' || data.status === 'unavailable') {
            setError('Desktop failed to start or is unavailable.')
            setIsLoading(false)
            setIsDemoLaunched(false)
            break
          }
        } catch (err) {
          setError('Error polling desktop status.')
          setIsLoading(false)
          setIsDemoLaunched(false)
          break
        }
        await new Promise(res => setTimeout(res, delay))
        if (firstPoll) {
          delay = 1000 // After first poll, always use 1s
          firstPoll = false
        }
      }
    } catch (error) {
      setError('Error during launch.')
      setIsLoading(false)
      setIsDemoLaunched(false)
    }
  }

  // Function to handle stopping the desktop
  const handleStopDesktop = async (id: string) => {
    setIsDemoLaunched(false)
    setIsLoading(true)
    const success = await stopVirtualDesktop(id)
    if (success) {
      setStreamUrl("")
      setTimeout(() => {
        setIsLoading(false)
        setStreamUrl("")
        onDesktopStopped()
      }, 800)
    } else {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full w-full rounded-lg border border-gray-200 bg-gray-50 overflow-hidden flex-col relative">
      <DemoHeader
        isDemoLaunched={isDemoLaunched}
        desktopId={desktopId}
        onStopDesktop={handleStopDesktop}
      />
      <DemoContent
        isLoading={isLoading}
        isDemoLaunched={isDemoLaunched}
        hasEverLaunchedDemo={hasEverLaunchedDemo}
        streamUrl={streamUrl}
        isLoggedIn={isLoggedIn}
        onLaunchDemo={launchDemo}
        error={error}
        ref={demoContentRef}
      />
      {isDemoLaunched && desktopId && (
        <div className="md:hidden w-full flex justify-center mt-4 mb-6">
          <button
            onClick={() => handleStopDesktop(desktopId)}
            className="inline-flex items-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
          >
            <ComputerDesktopIcon className="mr-2 h-4 w-4" />
            Stop Desktop
          </button>
        </div>
      )}
    </div>
  )
}

const DemoHeader = ({
  isDemoLaunched,
  desktopId,
  onStopDesktop,
}: {
  isDemoLaunched: boolean
  desktopId?: string
  onStopDesktop: (id: string) => Promise<void>
}) => (
  <div className="border-b border-gray-200 bg-white p-6">
    <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
      <div className="flex-shrink-0 md:max-w-xs">
        <h3 className="text-lg font-semibold text-gray-900">
          Try an interactive demo
        </h3>
        <p className="mt-2 text-sm text-gray-600">
          See how easy it is to deploy a virtual desktop with our API
        </p>

        {isDemoLaunched && desktopId && (
          <button
            onClick={() => onStopDesktop(desktopId)}
            className="mt-4 hidden md:inline-flex items-center rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
          >
            <ComputerDesktopIcon className="mr-2 h-4 w-4" />
            Stop Desktop
          </button>
        )}
      </div>
    </div>
  </div>
)

const loadingMessages = [
  'Requesting a new virtual desktop...',
  'Provisioning resources in the cloud...',
  'Booting up the operating system...',
  'Establishing a secure connection...',
  'Preparing your remote desktop experience...'
]

const LoadingState = ({ mode }: { mode: 'starting' | 'stopping' }) => {
  const [msgIdx, setMsgIdx] = useState(0)
  const [fade, setFade] = useState(true)
  const [showWaitMsg, setShowWaitMsg] = useState(false)

  useEffect(() => {
    if (mode !== 'starting') return
    const interval = setInterval(() => {
      setFade(false)
      setTimeout(() => {
        setMsgIdx((idx) => (idx + 1) % loadingMessages.length)
        setFade(true)
      }, 300)
    }, 2000)
    return () => clearInterval(interval)
  }, [mode])

  useEffect(() => {
    if (mode !== 'starting') return
    const timer = setTimeout(() => setShowWaitMsg(true), 5000)
    return () => clearTimeout(timer)
  }, [mode])

  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-gray-50">
      <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-indigo-600 mb-6"></div>
      {mode === 'starting' && (
        <>
          <div
            className={`transition-opacity duration-300 text-lg text-gray-700 font-medium ${fade ? 'opacity-100' : 'opacity-0'}`}
            style={{ minHeight: 32 }}
          >
            {loadingMessages[msgIdx]}
          </div>
          {showWaitMsg && (
            <div className="mt-2 text-sm text-gray-400">This may take up to a minute. Thank you for your patience!</div>
          )}
        </>
      )}
    </div>
  )
}

const DesktopIframe = ({ streamUrl, isLoading }: { streamUrl: string, isLoading: boolean }) => {
  return (
    <div className="w-full h-[400px] md:h-[500px] bg-black relative overflow-hidden flex items-center justify-center">
      <iframe
        src={streamUrl}
        className="w-full h-full"
        style={{ display: streamUrl && streamUrl !== 'about:blank' ? 'block' : 'none', border: 'none' }}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; clipboard-read; clipboard-write; fullscreen"
        allowFullScreen
        title="Virtual Desktop Stream"
      ></iframe>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800 text-white z-10">
          <div className="flex flex-col items-center">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-400 mb-3"></div>
            Preparing stream...
          </div>
        </div>
      )}
    </div>
  )
}

const InitialDemoState = ({ onLaunchDemo }: { onLaunchDemo: () => void }) => (
  <div className="h-full w-full flex items-center justify-center">
    <div className="text-center">
      <ComputerDesktopIcon className="mx-auto mb-4 h-16 w-16 text-gray-300" />
      <p className="text-center text-lg font-medium">
        Deploy a virtual desktop
      </p>
      <p className="mt-2 max-w-md text-center text-sm">
        Production ready, secure, and scalable
      </p>

      <button
        onClick={onLaunchDemo}
        className="mx-auto mt-6 flex items-center rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition-colors hover:bg-indigo-700"
      >
        <ComputerDesktopIcon className="mr-2 h-4 w-4" />
        Launch demo
      </button>
    </div>
  </div>
)

const PostDemoState = ({ isLoggedIn }: { isLoggedIn: boolean }) => (
  <div className="h-full w-full flex items-center justify-center">
    <div className="text-center">
      <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100">
        <ComputerDesktopIcon className="h-6 w-6 text-indigo-600" />
      </div>
      <h3 className="mb-2 text-lg font-medium text-gray-900">
        Ready to deploy your own?
      </h3>
      <p className="mb-4 text-sm text-gray-500">
        Create your first virtual desktop in a few clicks.
      </p>
      <Button
        href={isLoggedIn ? '/dashboard' : '/login'}
        className="inline-flex items-center rounded-lg bg-indigo-600 px-5 py-3 font-medium text-white transition-colors hover:bg-indigo-700"
      >
        Get started
        <ChevronRightIcon className="ml-2 h-5 w-5" />
      </Button>
    </div>
  </div>
)

const DemoContent = React.forwardRef<
  HTMLDivElement,
  {
    isLoading: boolean
    isDemoLaunched: boolean
    hasEverLaunchedDemo: boolean
    streamUrl: string
    isLoggedIn: boolean
    onLaunchDemo: () => void
    error?: string | null
  }
>(({ isLoading, isDemoLaunched, hasEverLaunchedDemo, streamUrl, isLoggedIn, onLaunchDemo, error }, ref) => {
  let content
  if (isLoading) {
    content = <LoadingState mode={isDemoLaunched ? 'starting' : 'stopping'} />
  } else if (error) {
    content = (
      <div className="flex flex-col items-center justify-center w-full h-full text-center p-8">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mb-4 animate-pulse text-red-500">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.008v.008H12v-.008Z" />
        </svg>
        <h3 className="text-xl font-semibold mb-2 text-red-600">Oops! Something went wrong.</h3>
        <p className="text-md text-gray-600">{error}</p>
      </div>
    )
  } else if (isDemoLaunched) {
    content = <DesktopIframe streamUrl={streamUrl} isLoading={isLoading} />
  } else {
    content = !hasEverLaunchedDemo ? (
      <InitialDemoState onLaunchDemo={onLaunchDemo} />
    ) : (
      <PostDemoState isLoggedIn={isLoggedIn} />
    )
  }
  return (
    <div ref={ref} className="flex-grow flex justify-center items-center min-h-[400px] max-h-[400px] md:min-h-[500px] md:max-h-[500px]">
      {content}
    </div>
  )
})
DemoContent.displayName = 'DemoContent'

// API functions
const deployVirtualDesktop = async (): Promise<DesktopLaunchResponse> => {
  try {
    const apiResponse = await fetch('/api/playground/desktop', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ timeoutMs: DESKTOP_TIMEOUT_MS })
    });

    const responseData = await apiResponse.json();

    if (!apiResponse.ok) {
      console.error('Backend API error:', responseData.error || `Status: ${apiResponse.status}`);
      // Handle error appropriately in the UI if needed
      return {
        id: '',
        status: 'error'
      };
    } else {
      // TODO: Maybe use the returned streamUrl and id?
      // Example: setStreamUrl(responseData.streamUrl); onDesktopDeployed(responseData.streamUrl, responseData.id);
      return {
        id: responseData.id,
        status: responseData.status
      };
    }
  } catch (error) {
    console.error('Error calling backend API:', error);
    // Handle fetch error appropriately
    return {
      id: '',
      status: 'error'
    };
  }
}

const stopVirtualDesktop = async (id: string): Promise<boolean> => {
  try {
    const response = await fetch('/api/playground/desktop', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id }),
    })

    if (!response.ok) {
      throw new Error('Failed to stop desktop')
    }

    return true
  } catch (error) {
    console.error('Error stopping desktop:', error)
    return false
  }
}

const getDetailsVirtualDesktop = async (id: string): Promise<{ status: string; stream_url?: string; error?: string }> => {
  try {
    const response = await fetch(`/api/playground/desktop?id=${id}`)
    const data = await response.json()
    if (!response.ok) {
      return { status: 'error', error: data.error || `Status: ${response.status}` }
    }
    return data
  } catch (error) {
    return { status: 'error', error: (error as Error).message }
  }
}
