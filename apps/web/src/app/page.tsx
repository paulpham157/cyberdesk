import { Container } from '@/components/container'
import { Footer } from '@/components/footer'
import { LogoCloud } from '@/components/logo-cloud'
import { Testimonials } from '@/components/testimonials'
import type { Metadata } from 'next'
import { Hero } from '../components/hero'
import PlaygroundDemo from './demo/page'
import Playground from './playground/page'

export const metadata: Metadata = {
  description:
    'Cyberdesk deploys virtual desktops for your computer agents with only in a few lines of code.',
}

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen w-full gap-6">
      <Hero />
      {/* <PlaygroundDemo /> */}
      <div className="mx-2 sm:mx-4 md:mx-6 lg:mx-8 xl:mx-10">
        <Playground />
      </div>
      <Footer />
    </div>
  )
}
