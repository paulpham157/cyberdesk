'use client'

import { Mark } from '@/components/logo'
import { clsx } from 'clsx'

export interface AppLogoProps {
  className?: string
  size?: 'small' | 'medium' | 'large'
  variant?: 'light' | 'dark'
}

export function AppLogo({ 
  className, 
  size = 'medium', 
  variant = 'dark' 
}: AppLogoProps) {
  const sizeClasses = {
    small: 'h-6 w-auto',
    medium: 'h-8 w-auto',
    large: 'h-10 w-auto',
  }

  // Use the Mark component from the existing logo.tsx
  return (
    <Mark 
      className={clsx(
        sizeClasses[size],
        variant === 'light' ? 'fill-white' : 'fill-black',
        className
      )} 
    />
  )
}
