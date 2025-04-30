export interface Profile {
  id: string;
  unkey_key_id?: string;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  current_period_end?: Date;
  subscription_status?: string;
  plan_id?: string;
  cancel_at_period_end?: boolean;
  created_at?: Date;
  updated_at?: Date;
}

// This interface matches the backend schema for cyberdesk_instances (see apps/api/src/db/schema.ts)
export interface CyberdeskInstance {
  id: string;
  user_id: string;
  created_at: string; // ISO string from DB
  updated_at?: string | null; // nullable
  status: 'pending' | 'running' | 'terminated' | 'error';
  timeout_at: string; // ISO string from DB
  stream_url?: string | null;
}