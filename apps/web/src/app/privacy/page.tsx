import { Container } from '@/components/container'
import { Footer } from '@/components/footer'
import { Gradient, GradientBackground } from '@/components/gradient'
import { Navbar } from '@/components/navbar'
import { Heading, Lead } from '@/components/text'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy | Cyberdesk',
  description:
    'Privacy Policy for Cyberdesk virtual desktop infrastructure and AI agents platform.',
}

function Header() {
  return (
    <Container className="mt-16">
      <Heading as="h1">Privacy Policy</Heading>
      <Lead className="mt-6 max-w-3xl">
        Last updated: March 27, 2025
      </Lead>
    </Container>
  )
}

export default function Privacy() {
  return (
    <>
      <GradientBackground>
        <Navbar />
        <Header />
        <Container className="mt-16 mb-24">
          <div className="prose prose-lg prose-gray mx-auto">
            <h2>1. Introduction</h2>
            <p>
              At Cyberdesk, we respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our virtual desktop infrastructure and AI agent services.
            </p>

            <h2>2. Information We Collect</h2>
            <p>
              We collect several types of information from and about users of our Services, including:
            </p>
            <ul>
              <li><strong>Personal Information:</strong> Name, email address, billing information, and other contact details you provide when registering for our Services.</li>
              <li><strong>Usage Data:</strong> Information about how you use our Services, including login times, features used, and interactions with our platform.</li>
              <li><strong>Device Information:</strong> Information about the devices you use to access our Services, including IP address, browser type, and operating system.</li>
              <li><strong>Virtual Desktop Content:</strong> Data generated or stored within your virtual desktop environment, including files, applications, and AI agent configurations.</li>
            </ul>

            <h2>3. How We Use Your Information</h2>
            <p>
              We use the information we collect for various purposes, including:
            </p>
            <ul>
              <li>Providing, maintaining, and improving our Services</li>
              <li>Processing your transactions and managing your account</li>
              <li>Communicating with you about our Services, updates, and support</li>
              <li>Analyzing usage patterns to enhance user experience</li>
              <li>Detecting, preventing, and addressing technical issues or security breaches</li>
              <li>Complying with legal obligations</li>
            </ul>

            <h2>4. Data Storage and Security</h2>
            <p>
              We implement appropriate technical and organizational measures to protect your personal data against unauthorized or unlawful processing, accidental loss, destruction, or damage. However, no method of transmission over the Internet or electronic storage is 100% secure, and we cannot guarantee absolute security.
            </p>

            <h2>5. Data Retention</h2>
            <p>
              We retain your personal information for as long as necessary to fulfill the purposes outlined in this Privacy Policy, unless a longer retention period is required or permitted by law. When determining how long to retain data, we consider the amount, nature, and sensitivity of the data, potential risk of harm from unauthorized use or disclosure, and applicable legal requirements.
            </p>

            <h2>6. Sharing Your Information</h2>
            <p>
              We may share your information in the following circumstances:
            </p>
            <ul>
              <li><strong>Service Providers:</strong> We may share your information with third-party vendors who provide services on our behalf, such as payment processing, data analysis, and customer service.</li>
              <li><strong>Business Transfers:</strong> If we are involved in a merger, acquisition, or sale of assets, your information may be transferred as part of that transaction.</li>
              <li><strong>Legal Requirements:</strong> We may disclose your information if required to do so by law or in response to valid requests by public authorities.</li>
              <li><strong>With Your Consent:</strong> We may share your information with third parties when you have given us your consent to do so.</li>
            </ul>

            <h2>7. Your Rights</h2>
            <p>
              Depending on your location, you may have certain rights regarding your personal data, including:
            </p>
            <ul>
              <li>The right to access and receive a copy of your personal data</li>
              <li>The right to rectify or update your personal data</li>
              <li>The right to erase your personal data</li>
              <li>The right to restrict processing of your personal data</li>
              <li>The right to data portability</li>
              <li>The right to object to processing of your personal data</li>
              <li>The right to withdraw consent</li>
            </ul>

            <h2>8. Children&apos;s Privacy</h2>
            <p>
              Our Services are not intended for children under the age of 16, and we do not knowingly collect personal information from children under 16. If we learn we have collected or received personal information from a child under 16, we will delete that information.
            </p>

            <h2>9. International Data Transfers</h2>
            <p>
              Your information may be transferred to, and maintained on, computers located outside of your state, province, country, or other governmental jurisdiction where the data protection laws may differ from those of your jurisdiction. If you are located outside the United States and choose to provide information to us, please note that we transfer the data to the United States and process it there.
            </p>

            <h2>10. Cookies and Similar Technologies</h2>
            <p>
              We use cookies and similar tracking technologies to track activity on our Services and hold certain information. Cookies are files with a small amount of data which may include an anonymous unique identifier. You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
            </p>

            <h2>11. Changes to This Privacy Policy</h2>
            <p>
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the &quot;Last updated&quot; date. You are advised to review this Privacy Policy periodically for any changes.
            </p>

            <h2>12. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy, please contact us at privacy@cyberdesk.io.
            </p>
          </div>
        </Container>
        <Footer />
      </GradientBackground>
    </>
  )
}
