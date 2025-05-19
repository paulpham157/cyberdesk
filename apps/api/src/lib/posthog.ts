import { PostHog } from 'posthog-node'
import * as dotenv from 'dotenv';

// Ensure environment variables are loaded
dotenv.config();

const POSTHOG_API_KEY = process.env.POSTHOG_API_KEY;

if (!POSTHOG_API_KEY) {
    throw new Error('POSTHOG_API_KEY is not set');
}

const POSTHOG_HOST = process.env.POSTHOG_HOST || 'https://us.i.posthog.com';

const client = new PostHog(
    POSTHOG_API_KEY,
    { host: POSTHOG_HOST, enableExceptionAutocapture: true },
)

export default client; 