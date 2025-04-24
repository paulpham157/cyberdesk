'use client';

import { Button } from '@/components/button'
import { Link } from '@/components/link'
import { Mark } from '@/components/logo'
import { Checkbox, Field, Input, Label } from '@headlessui/react'
import { CheckIcon } from '@heroicons/react/16/solid'
import { clsx } from 'clsx'
import { supabase } from '@/utils/supabase/client'
import { useRouter } from 'next/navigation'

export function LoginForm() {

  const router = useRouter()
  const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    
    if (error) {
      console.error('Error signing in with Google:', error.message)
    }
  }

  return (
    <>
      <form action="#" method="POST" className="p-7 sm:pl-11 sm:pr-11 sm:pt-11 relative">

        <div className="absolute right-[20px] top-[20px] text-black cursor-pointer " onClick={() => {router.back()}}>
          <Button type="button" variant="outline" className="w-full">
            Close
          </Button>
        </div>
        <div className="flex items-start">
          <Link href="/" title="Home">
            <Mark className="h-9 fill-black" />
          </Link>
        </div>
        <h1 className="mt-8 text-base/6 font-medium">Welcome to Cyberdesk!</h1>
        <p className="mt-1 text-sm/5 text-gray-600">
          Sign in to your account to continue.
        </p>
        {/* <Field className="mt-8 space-y-3">
          <Label className="text-sm/5 font-medium">Email</Label>
          <Input
            required
            autoFocus
            type="email"
            name="email"
            className={clsx(
              'block w-full rounded-lg border border-transparent ring-1 shadow-sm ring-black/10',
              'px-[calc(--spacing(2)-1px)] py-[calc(--spacing(1.5)-1px)] text-base/6 sm:text-sm/6',
              'data-focus:outline data-focus:outline-2 data-focus:-outline-offset-1 data-focus:outline-black',
            )}
          />
        </Field>
        <Field className="mt-8 space-y-3">
          <Label className="text-sm/5 font-medium">Password</Label>
          <Input
            required
            type="password"
            name="password"
            className={clsx(
              'block w-full rounded-lg border border-transparent ring-1 shadow-sm ring-black/10',
              'px-[calc(--spacing(2)-1px)] py-[calc(--spacing(1.5)-1px)] text-base/6 sm:text-sm/6',
              'data-focus:outline data-focus:outline-2 data-focus:-outline-offset-1 data-focus:outline-black',
            )}
          />
        </Field>

        <div className="mt-8">
          <Button type="submit" className="w-full">
            Sign in
          </Button>
        </div> */}
      </form>

      <div className="px-7 sm:px-11 pb-7 sm:pb-11 pt-0">
        <div className="relative mt-6">
          <div className="absolute inset-0 flex items-center" aria-hidden="true">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-sm font-medium leading-6">
            <span className="bg-white px-6 text-gray-500">Continue with</span>
          </div>
        </div>

        <div className="mt-6">
          <Button
            type="button"
            variant="outline"
            className="w-full flex items-center justify-center gap-3"
            onClick={signInWithGoogle}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              <path fill="none" d="M1 1h22v22H1z" />
            </svg>
            Sign in with Google
          </Button>
        </div>
      </div>

    </>
  )
}
