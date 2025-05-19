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
import { supabase } from '@/utils/supabase/client'
import CONFIG from '../../config'
import { TooltipIconButton } from './tooltip-icon-button'

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

function GitHubIcon(props: React.ComponentPropsWithoutRef<'svg'>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M12 2C6.477 2 2 6.484 2 12.021c0 4.426 2.865 8.184 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.091-.647.35-1.088.636-1.339-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.025A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.025 2.748-1.025.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.847-2.338 4.695-4.566 4.944.36.31.68.921.68 1.857 0 1.34-.012 2.421-.012 2.751 0 .268.18.579.688.481C19.138 20.2 22 16.447 22 12.021 22 6.484 17.523 2 12 2Z" />
    </svg>
  )
}

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

function MobileNav({ githubIcon }: { githubIcon?: React.ReactNode }) {
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
        {githubIcon && (
          <div className="flex justify-start">{githubIcon}</div>
        )}
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
        <PlusGridRow className="relative flex justify-between items-center">
          <div className="relative flex gap-3 items-center">
            <PlusGridItem className="py-3">
              <Link href="/" title="Home" className="flex items-center gap-3">
                <AppLogo size="large" className="h-9" />
                <LogoText/>
              </Link>
            </PlusGridItem>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/cyberdesk-hq/cyberdesk"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center"
              aria-label="Star us on GitHub"
            >
              <TooltipIconButton
                tooltip="Star us on GitHub"
                className="text-gray-950 hover:text-black transition-colors duration-200"
                style={{ padding: 0 }}
              >
                <GitHubIcon className="size-9" />
              </TooltipIconButton>
            </a>
            <DesktopNav />
            <MobileNavButton />
          </div>
        </PlusGridRow>
      </PlusGrid>
      <MobileNav githubIcon={
        <a
          href="https://github.com/cyberdesk-hq/cyberdesk"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Star us on GitHub"
          className="flex items-center mb-4"
        >
          <TooltipIconButton
            tooltip="Star us on GitHub"
            className="text-gray-950 hover:text-black transition-colors duration-200"
            style={{ padding: 0 }}
          >
            <GitHubIcon className="size-9" />
          </TooltipIconButton>
        </a>
      } />
    </Disclosure>
  )
}
