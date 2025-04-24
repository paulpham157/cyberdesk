import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react'
import { MinusSmallIcon, PlusSmallIcon } from '@heroicons/react/24/outline'

const faqs = [
  {
    question: "How do I get started with Cyberdesk?",
    answer:
      "Simply subscribe to our Pro plan, and you'll immediately gain access to all features. You can then create your API key and start deploying virtual desktops that your computer agents can seamlessly control like a human.",
  },
  {
    question: "Is there a money back guarantee?",
    answer:
      "Yes, we offer a 30-day money-back guarantee. If you're not satisfied with our service, you can let us know and we'll process a refund. You can cancel your subscription at any time.",
  },
  {
    question: "Can I increase my limits?",
    answer:
      "Yes, you can increase your limits by upgrading to a higher-tier plan. Contact us for more information.",
  },
  {
    question: "What is the operating system of the virtual desktop?",
    answer:
      "The virtual desktop is based on Ubuntu. This ensures a stable and secure environment for your AI agents.",
  },
  {
    question: "What programming languages and frameworks are supported?",
    answer:
      "Our REST API can be called from anywhere, regardless of the programming language you're using. SDK support for popular languages is coming soon.",
  },
  {
    question: "How do I connect my AI agent to the virtual desktop?",
    answer:
      "Our API has endpoints for computer and bash actions, specifically tailored for CUA (Computer-Using Agent) agents. These endpoints allow your AI to interact with the virtual desktop just like a human would.",
  },
  {
    question: "Is there a free trial available?",
    answer:
      "Contact us about this, we'd love to chat about your specific needs and how we can help you get started with Cyberdesk.",
  }
]

export function FAQSection() {
  return (
    <div className="bg-white">
      <div className="mx-auto max-w-7xl px-6 py-0 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-xl tracking-tight text-gray-900 sm:text-3xl">
            Frequently asked questions
          </h2>
          <dl className="mt-6 divide-y divide-gray-900/10">
            {faqs.map((faq) => (
              <Disclosure key={faq.question} as="div" className="py-3 first:pt-0 last:pb-0">
                <dt>
                  <DisclosureButton className="group flex w-full items-start justify-between text-left text-gray-900">
                    <span className="text-base/7 font-medium">{faq.question}</span>
                    <span className="ml-6 flex h-7 items-center">
                      <PlusSmallIcon aria-hidden="true" className="size-6 group-data-[open]:hidden" />
                      <MinusSmallIcon aria-hidden="true" className="size-6 group-[&:not([data-open])]:hidden" />
                    </span>
                  </DisclosureButton>
                </dt>
                <DisclosurePanel as="dd" className="mt-2 pr-12">
                  <p className="text-base/7 text-gray-600">{faq.answer}</p>
                </DisclosurePanel>
              </Disclosure>
            ))}
          </dl>
        </div>
      </div>
    </div>
  )
}
