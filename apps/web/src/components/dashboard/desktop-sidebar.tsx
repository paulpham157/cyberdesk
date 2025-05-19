'use client'

import { navigation, classNames } from './sidebar-navigation'
import { AppLogo } from '@/components/shared/app-logo'
import { ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'

interface DesktopSidebarProps {
  userEmail?: string;
}

export function DesktopSidebar({ userEmail }: DesktopSidebarProps) {
  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
      {/* Sidebar component, swap this element with another sidebar if you like */}
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6">
        <div className="flex h-16 shrink-0 items-center">
          <a href="/" className="cursor-pointer">
            <AppLogo variant="light" size="medium" />
          </a>
        </div>
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => (
                  <li key={item.name}>
                    <a
                      href={item.href}
                      target={item.external ? '_blank' : undefined}
                      rel={item.external ? 'noopener noreferrer' : undefined}
                      className={classNames(
                        item.current
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                        'group flex gap-x-3 rounded-md p-2 text-sm/6 font-semibold',
                      )}
                    >
                      <item.icon aria-hidden="true" className="size-6 shrink-0" />
                      <span className="flex-1">{item.name}</span>
                      {item.external && (
                        <ArrowTopRightOnSquareIcon aria-hidden="true" className="size-4 text-gray-400 self-center" />
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </li>
            {/* <li>
              <div className="text-xs/6 font-semibold text-gray-400">Your teams</div>
              <ul role="list" className="-mx-2 mt-2 space-y-1">
                {teams.map((team) => (
                  <li key={team.name}>
                    <a
                      href={team.href}
                      className={classNames(
                        team.current
                          ? 'bg-gray-800 text-white'
                          : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                        'group flex gap-x-3 rounded-md p-2 text-sm/6 font-semibold',
                      )}
                    >
                      <span className="flex size-6 shrink-0 items-center justify-center rounded-lg border border-gray-700 bg-gray-800 text-[0.625rem] font-medium text-gray-400 group-hover:text-white">
                        {team.initial}
                      </span>
                      <span className="truncate">{team.name}</span>
                    </a>
                  </li>
                ))}
              </ul>
            </li> */}
            <li className="-mx-6 mt-auto">
              <div
                className="flex items-center gap-x-4 px-6 py-3 text-sm/6 font-semibold text-white"
              >
                <div className="flex items-center justify-center size-8 rounded-full bg-gray-800 text-white">
                  {userEmail ? userEmail.charAt(0).toUpperCase() : '?'}
                </div>
                <span className="sr-only">Your profile</span>
                <span aria-hidden="true" className="truncate">{userEmail || 'Loading...'}</span>
              </div>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  )
}
