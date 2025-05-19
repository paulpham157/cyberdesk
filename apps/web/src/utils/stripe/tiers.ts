// Define the tier type
export interface Tier {
  name: string;
  slug: string;
  description: string;
  priceMonthly: number;
  href: string;
  highlights: { description: string; disabled?: boolean }[];
  features: {
    section: string;
    name: string;
    value: string | number | boolean;
  }[];
}

// Define the tiers configuration
export const tiers: Tier[] = [
  {
    name: 'Pro',
    slug: 'pro',
    description: 'Get started with deploying AI computer agents on up to 20 concurrent desktops',
    priceMonthly: 19.99,
    href: '#',
    highlights: [
      { description: '24 hour session per desktop launch' },
      { description: 'Up to 20 concurrent desktops' },
      { description: 'Unlimited desktop actions' },
      // { description: 'RadiantAI integrations', disabled: true },
      // { description: 'Competitor analysis', disabled: true },
    ],
    features: [
      { section: 'Features', name: 'Desktops', value: 3 },
      { section: 'Features', name: 'Deal progress boards', value: 5 },
      { section: 'Features', name: 'Sourcing platforms', value: 'Select' },
      { section: 'Features', name: 'Contacts', value: 100 },
      { section: 'Features', name: 'AI assisted outreach', value: false },
      { section: 'Analysis', name: 'Competitor analysis', value: false },
      { section: 'Analysis', name: 'Dashboard reporting', value: false },
      { section: 'Analysis', name: 'Community insights', value: false },
      { section: 'Analysis', name: 'Performance analysis', value: false },
      { section: 'Support', name: 'Email support', value: true },
      { section: 'Support', name: '24 / 7 call center support', value: false },
      { section: 'Support', name: 'Dedicated account manager', value: false },
    ],
  }
];
