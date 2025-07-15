import { Container } from '@/components/container'
import { Footer } from '@/components/footer'
import { Gradient, GradientBackground } from '@/components/gradient'
import { Navbar } from '@/components/navbar'
import { Heading, Lead } from '@/components/text'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service | Cyberdesk',
  description:
    'Terms of Service for Cyberdesk virtual desktop infrastructure and AI agents platform.',
}

function Header() {
  return (
    <Container className="mt-16">
      <Heading as="h1">Terms of Service</Heading>
      <Lead className="mt-6 max-w-3xl">
        Last updated: March 27, 2025
      </Lead>
    </Container>
  )
}

export default function Terms() {
  return (
    <>
      <GradientBackground>
        <Navbar />
        <Header />
        <Container className="mt-16 mb-24">
          <div className="prose prose-lg prose-gray mx-auto">
            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing or using Cyberdesk&apos;s virtual desktop infrastructure and AI agent services (&quot;Services&quot;), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our Services.
            </p>

            <h2>2. Description of Services</h2>
            <p>
              Cyberdesk provides cloud-based virtual desktop infrastructure and AI agent deployment services. Our platform allows users to deploy, manage, and interact with autonomous AI agents on virtual desktops.
            </p>

            <h2>3. Account Registration</h2>
            <p>
              To access certain features of our Services, you must register for an account. You agree to provide accurate, current, and complete information during the registration process and to update such information to keep it accurate, current, and complete.
            </p>

            <h2>4. User Responsibilities</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account or any other breach of security.
            </p>

            <h2>5. Subscription and Billing</h2>
            <p>
              Certain aspects of our Services require payment of fees. All fees are specified on our pricing page and are subject to change with notice. You agree to pay all fees in accordance with the billing terms in effect at the time a fee is due.
            </p>

            <h2>6. Usage Limitations</h2>
            <p>
              Your use of the Services must comply with all applicable laws and regulations. You may not use the Services for any illegal or unauthorized purpose, including but not limited to violating any intellectual property rights.
            </p>

            <h2>7. Data and Security</h2>
            <p>
              We implement reasonable security measures to protect your data, but we cannot guarantee absolute security. You are responsible for backing up your data and ensuring that your use of our Services does not expose your systems to security risks.
            </p>

            <h2>8. Intellectual Property</h2>
            <p>
              All content, features, and functionality of our Services, including but not limited to text, graphics, logos, and software, are owned by Cyberdesk and are protected by intellectual property laws. You may not reproduce, distribute, or create derivative works without our prior written consent.
            </p>

            <h2>9. Termination</h2>
            <p>
              We reserve the right to suspend or terminate your access to the Services at any time for any reason, including but not limited to a violation of these Terms. Upon termination, your right to use the Services will immediately cease.
            </p>

            <h2>10. Disclaimer of Warranties</h2>
            <p>
              THE SERVICES ARE PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED. WE DO NOT WARRANT THAT THE SERVICES WILL BE UNINTERRUPTED OR ERROR-FREE.
            </p>

            <h2>11. Limitation of Liability</h2>
            <p>
              IN NO EVENT SHALL CYBERDESK BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY.
            </p>

            <h2>12. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless Cyberdesk and its officers, directors, employees, and agents, from and against any claims, liabilities, damages, losses, and expenses arising out of or in any way connected with your use of the Services.
            </p>

            <h2>13. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the State of California, without regard to its conflict of law provisions.
            </p>

            <h2>14. Changes to Terms</h2>
            <p>
              We reserve the right to modify these Terms at any time. We will provide notice of any material changes by posting the new Terms on our website. Your continued use of the Services after such modifications constitutes your acceptance of the revised Terms.
            </p>

            <h2>15. Contact Information</h2>
            <p>
              If you have any questions about these Terms, please contact us at mahmoud@cyberdesk.io.
            </p>
          </div>
        </Container>
        <Footer />
      </GradientBackground>
    </>
  )
}
