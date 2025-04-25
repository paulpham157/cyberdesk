# Created by Unkey's toolbox

This API is built with speed, and security in mind. The API is built with [Hono](https://hono.dev), [Unkey](https://unkey.com) and [Supabase](https://supabase.com) with hosting on [Fly.io](https://fly.io).

## Getting Started

You will need a free account for both Unkey and Supabase to run this project.

### Unkey

For Unkey you will need your API ID and a root key scoped to:

- Create Key
- Create Namespace
- Limit

You can of course add more scopes as required.

### Supabase

For Supabase, you'll need to create a project and get your:

- Supabase URL
- Supabase Anon Key
- Supabase Connection String (found in the Database settings under Connection Pooling)

## Environment Variables

To run this project, you will need to add the following environment variables to your .dev.vars file

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_CONNECTION_STRING=postgres://postgres:your-password@your-project-id.supabase.co:5432/postgres?pgbouncer=true
UNKEY_API_ID=UNKEY_API_ID
UNKEY_ROOT_KEY=UNKEY_ROOT_KEY
```

## Usage

Make sure that you have run:

```bash
npm run db:generate
npm run db:push
```

You can then run `npm run dev`

Then you will have access to the following routes:

`/keys/create` - To create an API key to use with the other endpoints.

Then the desktop routes (all under the `/v1` prefix):

```bash
/v1/desktop                      # Create a new desktop instance
/v1/desktop/{id}/stop            # Stop a desktop instance
/v1/desktop/{id}/computer-action # Perform a computer action
/v1/desktop/{id}/bash-action     # Execute a bash command
```

You also have access to the open-api spec found at [http://localhost:8787/open-api](http://localhost:8787/open-api)
