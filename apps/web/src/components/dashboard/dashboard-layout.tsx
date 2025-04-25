'use client'

import { useState, type ReactNode } from 'react'
import { MobileSidebar } from './mobile-sidebar'
import { DesktopSidebar } from './desktop-sidebar'
import { MobileHeader } from './mobile-header'

interface DashboardLayoutProps {
  children: ReactNode;
  userEmail?: string;
}

export function DashboardLayout({ children, userEmail }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div>
      <MobileSidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <DesktopSidebar userEmail={userEmail} />
      <MobileHeader setSidebarOpen={setSidebarOpen} />

      <main className="py-10 lg:pl-72">
        <div className="px-4 sm:px-6 lg:px-8">{children}</div>
      </main>
    </div>
  )
}
