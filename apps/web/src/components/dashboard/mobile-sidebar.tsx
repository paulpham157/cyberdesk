'use client'

import { Dialog, DialogBackdrop, DialogPanel, TransitionChild } from '@headlessui/react'
import { XMarkIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline'
import { navigation, classNames } from './sidebar-navigation'
import { AppLogo } from '@/components/shared/app-logo'

interface MobileSidebarProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
}

export function MobileSidebar({ sidebarOpen, setSidebarOpen }: MobileSidebarProps) {
  return (
    <Dialog open={sidebarOpen} onClose={setSidebarOpen} className="relative z-50 lg:hidden">
      <DialogBackdrop
        transition
        className="fixed inset-0 bg-gray-900/80 transition-opacity duration-300 ease-linear data-[closed]:opacity-0"
      />

      <div className="fixed inset-0 flex">
        <DialogPanel
          transition
          className="relative mr-16 flex w-full max-w-xs flex-1 transform transition duration-300 ease-in-out data-[closed]:-translate-x-full"
        >
          <TransitionChild>
            <div className="absolute left-full top-0 flex w-16 justify-center pt-5 duration-300 ease-in-out data-[closed]:opacity-0">
              <button type="button" onClick={() => setSidebarOpen(false)} className="-m-2.5 p-2.5">
                <span className="sr-only">Close sidebar</span>
                <XMarkIcon aria-hidden="true" className="size-6 text-white" />
              </button>
            </div>
          </TransitionChild>
          {/* Sidebar component, swap this element with another sidebar if you like */}
          <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6 pb-2 ring-1 ring-white/10">
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
              </ul>
            </nav>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  )
}
