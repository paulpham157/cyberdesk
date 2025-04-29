'use client'

import { Button } from '@/components/button'
import { supabase } from '@/utils/supabaseClient'
import { ComputerDesktopIcon } from '@heroicons/react/24/outline'
import { ChevronRightIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/solid'
import React, { useEffect, useState, useRef, useCallback, forwardRef } from 'react'

// Constants
const FALLBACK_VIDEO_URL = ''
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
  const [streamUrl, setStreamUrl] = useState<string>(FALLBACK_VIDEO_URL)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [isDemoLaunched, setIsDemoLaunched] = useState(false)
  const [hasEverLaunchedDemo, setHasEverLaunchedDemo] = useState(false)
  const demoContentRef = useRef<HTMLDivElement>(null)
  const [vmStatus, setVmStatus] = useState<string>('')
  // Set isDemoLaunched based on desktopId prop
  useEffect(() => {
    if (desktopId) {
      setIsDemoLaunched(true)
      setHasEverLaunchedDemo(true)
    }
  }, [desktopId])

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

  // Effect for polling desktop status when pending
  useEffect(() => {
    let timeoutId: NodeJS.Timeout | null = null;

    const pollDesktopStatus = async () => {
      if (!desktopId) {
        console.warn('Polling stopped: desktopId is missing.');
        setIsLoading(false);
        setVmStatus('error'); // Cannot poll without ID
        return;
      }

      try {
        console.log(`Polling status for desktop ID: ${desktopId}`);
        const response = await fetch(`/api/playground/desktop?id=${desktopId}`);
        
        // Check specifically for API route errors (non-200)
        if (!response.ok) {
            console.error(`API responded with status ${response.status} for ID ${desktopId}`);
            let errorData = { status: 'error', stream_url: '' }; 
            try {
              errorData = await response.json();
            } catch(e) { /* Ignore JSON parsing error if body is empty */ }
            setVmStatus(errorData.status || 'error'); 
            setStreamUrl(errorData.stream_url || FALLBACK_VIDEO_URL); 
            setIsLoading(false);
            return; // Stop polling on server error
        }

        const data = await response.json();
        console.log('Polling response:', data);

        if (data.status === 'pending') {
          // Still pending, poll again after delay
          timeoutId = setTimeout(pollDesktopStatus, 2000);
        } else {
          // Status is no longer pending (e.g., 'ready', 'error', 'stopped', 'unavailable')
          setVmStatus(data.status || 'error'); // Use 'error' as fallback
          setStreamUrl(data.stream_url || (data.status === 'ready' ? FALLBACK_VIDEO_URL : 'about:blank')); // Provide fallback URL if ready but empty, otherwise blank
          setIsLoading(false); // Loading is complete
          console.log(`Polling finished for ${desktopId}. Final status: ${data.status}`);
        }
      } catch (error) {
        console.error(`Error polling desktop status for ID ${desktopId}:`, error);
        setVmStatus('error');
        setStreamUrl(FALLBACK_VIDEO_URL); // Fallback URL on error
        setIsLoading(false);
        // Stop polling on fetch/parse error
      }
    };

    if (vmStatus === 'pending' && desktopId) {
        console.log(`Starting polling for desktop ID: ${desktopId}`);
        setIsLoading(true); // Ensure loading is true when polling starts
        pollDesktopStatus();
    } else {
      // Optional: Ensure loading is false if status is not pending *unless* explicitly set to loading elsewhere.
      // if(isLoading && vmStatus !== 'loading') {
      //      setIsLoading(false);
      // }
    }

    // Cleanup function: clear timeout if component unmounts or dependencies change
    return () => {
      if (timeoutId) {
        console.log(`Clearing polling timeout for desktop ID: ${desktopId}`);
        clearTimeout(timeoutId);
      }
    };
    // Ensure all state setters used within the effect are listed if required by linting rules,
    // or disable the rule for this line. desktopId and vmStatus are the key drivers.
  }, [vmStatus, desktopId, setIsLoading, setStreamUrl, setVmStatus]);

  // Function to launch the demo
  const launchDemo = async () => {
    setIsLoading(true);
    setIsDemoLaunched(true);
    setHasEverLaunchedDemo(true);
    setVmStatus('loading'); // Indicate initial loading process

    // Check if we're on mobile (using the same logic as in DesktopIframe)
    const isMobile = window.innerWidth < 768;
    
    // Scroll to the demo content only on mobile
    if (demoContentRef.current) {
      if (isMobile) {
        // On mobile, scroll to the top of the demo content
        demoContentRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        // On desktop, scroll to center the demo content
        demoContentRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    try {
      const { status, id } = await deployVirtualDesktop();
      console.log("Deploy response:", { status, id });

      // Set initial status from deploy call
      setVmStatus(status);
      if (status !== 'error' && id) {
        if (onDesktopDeployed) {
          onDesktopDeployed(id); // Pass ID up only on success
        }
      } else {
          // Handle error from deployVirtualDesktop itself (e.g., status was 'error' or id was missing)
          if(status === 'error') {
          console.error("Deployment failed or returned invalid data", { status, id })
          setIsLoading(false);
          setStreamUrl(FALLBACK_VIDEO_URL);
          setVmStatus('error'); // Ensure status reflects the error
          // onDesktopStopped(); // Reset UI state
      }
    }
    } catch (error) {
      console.error('Error during launchDemo action:', error);
      setVmStatus('error');
      setStreamUrl(FALLBACK_VIDEO_URL);
      setIsLoading(false);
      // onDesktopStopped(); // Reset UI
    }

    // REMOVED: Simulate minimum loading time for better UX
    // setTimeout(() => setIsLoading(false), 800)
  }

  // Function to handle stopping the desktop
  const handleStopDesktop = async (id: string) => {
    setIsLoading(true)
    const success = await stopVirtualDesktop(id)

    if (success) {
      // Show a placeholder or different content after stopping
      setStreamUrl('about:blank')
      setTimeout(() => {
        setIsDemoLaunched(false)
        setIsLoading(false)
        setStreamUrl(FALLBACK_VIDEO_URL)
        // Call the parent component's callback to handle any parent state updates
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
        vmStatus={vmStatus}
        ref={demoContentRef}
      />
      
      {/* Mobile stop button - only visible on mobile devices */}
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

const LoadingState = () => (
  <div className="flex h-full w-full items-center justify-center bg-gray-50">
    <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-indigo-600"></div>
  </div>
)

const DesktopIframe = ({ streamUrl, vmStatus,isLoading }: { streamUrl: string, vmStatus: string, isLoading: boolean }) => {
  const [scale, setScale] = useState(0.5);
  const [isMobile, setIsMobile] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Detect if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  // Calculate and set the optimal scale based on container size
  const updateScale = useCallback(() => {
    // Don't calculate scale if showing error or not ready/loading
    if (!containerRef.current || vmStatus === 'error' || vmStatus === 'unavailable') return;
    
    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = containerRef.current.clientHeight;
    
    // Calculate how much we need to scale down to fit
    const widthScale = (containerWidth * 0.85) / 1024;
    const heightScale = (containerHeight * 0.85) / 768;
    
    // Use the smaller scale to ensure it fits both dimensions
    const optimalScale = Math.min(widthScale, heightScale);
    
    setScale(Math.max(0.1, Math.min(1.0, optimalScale)));
  }, [vmStatus]); // Add vmStatus dependency


  // Set up resize observer to update scale when container size changes
  useEffect(() => {
    // Don't observe if showing error or not ready/loading
    if (!containerRef.current || vmStatus === 'error' || vmStatus === 'unavailable') return;
    
    updateScale();
    
    const resizeObserver = new ResizeObserver(() => {
      updateScale();
    });
    
    resizeObserver.observe(containerRef.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, [updateScale, vmStatus]); // Add vmStatus dependency


  return (
    <div 
      ref={containerRef}
      className="w-full h-[400px] md:h-[500px] bg-black relative overflow-hidden" // Added relative and overflow-hidden
    >
      {vmStatus === 'error' ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 text-center p-4">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mb-4 animate-pulse text-red-500">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.008v.008H12v-.008Z" />
          </svg>
          <h3 className="text-xl font-semibold mb-2 text-red-600">Oops! Something went wrong.</h3>
          <p className="text-md text-gray-600">An error has occurred, please try again later.</p>
        </div>
      ) : (
        <div 
          className="w-full h-full flex items-center justify-center overflow-auto"
          style={{ 
            alignItems: isMobile ? 'flex-start' : 'center',
            paddingTop: isMobile ? '60px' : '0'
          }}
        >
          <div 
            style={{ 
              transform: `scale(${scale})`,
              transformOrigin: isMobile ? 'top center' : 'center center',
              transition: 'transform 0.3s ease-out', // Added smooth transition
            }}
          >
            <iframe
              src={streamUrl}
              width={1024}
              height={768}
              style={{ border: 'none', display: vmStatus === 'ready' ? 'block' : 'none' }} // Hide iframe until ready
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; clipboard-read; clipboard-write; fullscreen"
              allowFullScreen
              title="Virtual Desktop Stream" // Added title for accessibility
            ></iframe>
            {/* Optional: Add a loading indicator while vmStatus is 'loading' */}
            {isLoading && (
              <div className="w-[1024px] h-[768px] flex items-center justify-center bg-gray-800 text-white">
                <div className="flex flex-col items-center">
                  <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-indigo-400 mb-3"></div>
                  Preparing stream...
                </div>
              </div>
            )}
             {/* Optional: Add unavailable state */}
             {vmStatus === 'unavailable' && (
              <div className="w-[1024px] h-[768px] flex items-center justify-center bg-gray-900 text-gray-400">
                 <div className="flex flex-col items-center text-center p-4">
                   <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 mb-4 text-gray-500">
                     <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                   </svg>
                  <h3 className="text-lg font-medium mb-1">Desktop Unavailable</h3>
                  <p className="text-sm">The virtual desktop could not be started or is no longer available.</p>
                 </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

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
    vmStatus: string
    isLoggedIn: boolean
    onLaunchDemo: () => void
  }
>(({
  isLoading,
  isDemoLaunched,
  hasEverLaunchedDemo,
  streamUrl,
  vmStatus,
  isLoggedIn,
  onLaunchDemo,
}, ref) => {
  let content;
  
  if (isLoading) {
    content = <LoadingState />;
  } else if (isDemoLaunched) {
    content = <DesktopIframe streamUrl={streamUrl} vmStatus={vmStatus} isLoading={isLoading} />;
  } else {
    content = !hasEverLaunchedDemo ? (
      <InitialDemoState onLaunchDemo={onLaunchDemo} />
    ) : (
      <PostDemoState isLoggedIn={isLoggedIn} />
    );
  }
  
  return (
    <div ref={ref} className="flex-grow flex justify-center items-center min-h-[400px] max-h-[400px] md:min-h-[500px] md:max-h-[500px]">
        {content}
    </div>
  );
})

DemoContent.displayName = 'DemoContent';

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
      console.log('Backend API success:', responseData);
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
    console.log(`[stopVirtualDesktop] Calling fetch with id: ${id}`);
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
