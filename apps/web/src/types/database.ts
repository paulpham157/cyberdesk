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

export interface DesktopInstance {
  id: string;
  remote_id: string;
  user_id: string;
  stream_url: string;
  created_at?: Date;
  ended_at?: Date;
}
