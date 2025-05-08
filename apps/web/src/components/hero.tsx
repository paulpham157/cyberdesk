'use client';

import { Button } from '@/components/button'
import { Container } from '@/components/container'
import { Gradient } from '@/components/gradient'
import { Link } from '@/components/link'
import { Navbar } from '@/components/navbar'
import { ChevronRightIcon } from '@heroicons/react/16/solid'
import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { supabase } from '@/utils/supabaseClient'
import CONFIG from '../../config';

export function Hero() {
  const router = useRouter()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const { data } = await supabase.auth.getSession()
        setIsLoggedIn(!!data.session)
      } catch (error) {
        console.error('Error checking auth status:', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    checkAuthStatus()
  }, [])
  return (
    <div className="relative">
      <Gradient className="absolute inset-2 bottom-0 rounded-4xl ring-1 ring-black/5 ring-inset" />
      <Container className="relative">
        <Navbar
          // banner={
          //   <Link
          //     href="/blog/radiant-raises-100m-series-a-from-tailwind-ventures"
          //     className="flex items-center gap-1 rounded-full bg-fuchsia-950/35 px-3 py-0.5 text-sm/6 font-medium text-white data-hover:bg-fuchsia-950/30"
          //   >
          //     Cyberdesk raises $100M Series A from Tailwind Ventures
          //     <ChevronRightIcon className="size-4" />
          //   </Link>
          // }
        />
        <div className="pt-16 pb-24 sm:pt-24 sm:pb-32 md:pt-32 md:pb-48">
          <h1 className="font-display text-4xl font-medium tracking-tight text-balance text-gray-950 sm:text-7xl/[0.8] md:text-8xl/[0.8]">
            Open source virtual desktops for AI agents
          </h1>
          <p className="mt-14 max-w-lg text-xl/7 font-medium text-gray-950/75 sm:text-2xl/8">
            Deploy AI agents on virtual desktops with a few lines of code.
          </p>
          <div className="mt-12 flex flex-col gap-x-6 gap-y-4 sm:flex-row">
            {!isLoading && (isLoggedIn ? (
              <Button href="/dashboard">Go to Dashboard</Button>
            ) : (
              <>
                <Button onClick={() => router.push('/login')}>Get started</Button>
                <Button variant="secondary" href={CONFIG.docsURL} target="_blank" rel="noopener noreferrer">
                  See docs
                </Button>
              </>
            ))}
          </div>
        </div>
      </Container>
    </div>
  )
}
