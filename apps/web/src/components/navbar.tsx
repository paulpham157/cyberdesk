'use client'

import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
} from '@headlessui/react'
import { Bars2Icon } from '@heroicons/react/24/solid'
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import { Link } from './link'
import { PlusGrid, PlusGridItem, PlusGridRow } from './plus-grid'
import { AppLogo } from '@/components/shared/app-logo'
import { LogoText } from './LogoText' // Import the new component
import { useEffect, useState } from 'react'
import { supabase } from '@/utils/supabaseClient'
import CONFIG from '../../config'

// Define types for our navigation links
interface NavLink {
  href: string;
  label: string;
  external?: boolean;
  isLogout?: boolean;
}

const staticLinks: NavLink[] = [
  { href: '/pricing', label: 'Pricing' },
  { href: CONFIG.docsURL, label: 'Docs', external: true },
  // { href: '/company', label: 'Company' },
  // { href: '/blog', label: 'Blog' },
]

function DesktopNav() {
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
  
  const authLinks: NavLink[] = isLoggedIn 
    ? [
        { href: '/dashboard', label: 'Go to Dashboard' },
        { href: '#', label: 'Log Out', isLogout: true }
      ]
    : [{ href: '/login', label: 'Login' }]
  
  const links = [...staticLinks, ...authLinks]
  
  return (
    <nav className="relative hidden lg:flex">
      {!isLoading && (
        links.map(({ href, label, external, isLogout }) => (
          <PlusGridItem key={`${href}-${label}`} className="relative flex">
            {isLogout ? (
              <button
                onClick={async () => {
                  await supabase.auth.signOut();
                  window.location.href = '/';
                }}
                className="flex items-center px-4 py-3 text-base font-medium text-gray-950 bg-blend-multiply data-hover:bg-black/[2.5%] cursor-pointer"
              >
                {label}
              </button>
            ) : (
              <Link
                href={href}
                target={external ? '_blank' : undefined}
                rel={external ? 'noopener noreferrer' : undefined}
                className="flex items-center px-4 py-3 text-base font-medium text-gray-950 bg-blend-multiply data-hover:bg-black/[2.5%]"
              >
                {label}
                {external && (
                  <ArrowTopRightOnSquareIcon className="ml-1 h-4 w-4 text-gray-500" aria-hidden="true" />
                )}
              </Link>
            )}
          </PlusGridItem>
        ))
      )}
    </nav>
  )
}

function MobileNavButton() {
  return (
    <DisclosureButton
      className="flex size-12 items-center justify-center self-center rounded-lg data-hover:bg-black/5 lg:hidden"
      aria-label="Open main menu"
    >
      <Bars2Icon className="size-6" />
    </DisclosureButton>
  )
}

function MobileNav() {
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
  
  const authLinks: NavLink[] = isLoggedIn 
    ? [
        { href: '/dashboard', label: 'Go to Dashboard' },
        { href: '#', label: 'Log Out', isLogout: true }
      ]
    : [{ href: '/login', label: 'Login' }]
  
  const links = [...staticLinks, ...authLinks]
  
  return (
    <DisclosurePanel className="lg:hidden">
      <div className="flex flex-col gap-6 py-4">
        {!isLoading && (
          links.map(({ href, label, external, isLogout }, linkIndex) => (
          <motion.div
            initial={{ opacity: 0, rotateX: -90 }}
            animate={{ opacity: 1, rotateX: 0 }}
            transition={{
              duration: 0.15,
              ease: 'easeInOut',
              rotateX: { duration: 0.3, delay: linkIndex * 0.1 },
            }}
            key={`${href}-${label}`}
          >
            {isLogout ? (
              <button
                onClick={async () => {
                  await supabase.auth.signOut();
                  window.location.href = '/';
                }}
                className="flex items-center text-base font-medium text-gray-950 cursor-pointer"
              >
                {label}
              </button>
            ) : (
              <Link 
                href={href} 
                target={external ? '_blank' : undefined}
                rel={external ? 'noopener noreferrer' : undefined}
                className="flex items-center text-base font-medium text-gray-950"
              >
                {label}
                {external && (
                  <ArrowTopRightOnSquareIcon className="ml-1 h-4 w-4 text-gray-500" aria-hidden="true" />
                )}
              </Link>
            )}
          </motion.div>
        )))
        }
      </div>
      <div className="absolute left-1/2 w-screen -translate-x-1/2">
        <div className="absolute inset-x-0 top-0 border-t border-black/5" />
        <div className="absolute inset-x-0 top-2 border-t border-black/5" />
      </div>
    </DisclosurePanel>
  )
}

export function Navbar({ banner }: { banner?: React.ReactNode }) {
  return (
    <Disclosure as="header" className="pt-12 sm:pt-16">
      <PlusGrid>
        <PlusGridRow className="relative flex justify-between">
          <div className="relative flex gap-3 items-center">
            <PlusGridItem className="py-3">
              <Link href="/" title="Home" className="flex items-center gap-3">
                <AppLogo size="large" className="h-9" />
                <LogoText/>
              </Link>
            </PlusGridItem>
          </div>
          <DesktopNav />
          <MobileNavButton />
        </PlusGridRow>
      </PlusGrid>
      <MobileNav />
    </Disclosure>
  )
}
