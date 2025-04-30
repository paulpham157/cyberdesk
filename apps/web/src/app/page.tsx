import { Container } from '@/components/container'
import { Footer } from '@/components/footer'
import { LogoCloud } from '@/components/logo-cloud'
import { Testimonials } from '@/components/testimonials'
import type { Metadata } from 'next'
import { Hero } from '../components/hero'
import PlaygroundDemo from './demo/page'


export const metadata: Metadata = {
  description:
    'Cyberdesk deploys virtual desktops for your computer agents with only in a few lines of code.',
}

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen w-full gap-6">
      <Hero />
      <PlaygroundDemo />
      <Footer />
    </div>
  )
}
