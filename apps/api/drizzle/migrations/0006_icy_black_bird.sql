DO $$ BEGIN
 CREATE TYPE "public"."instance_status" AS ENUM('pending', 'running', 'completed', 'error');
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "cyberdesk_instances" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"created_at" timestamp DEFAULT now(),
	"updated_at" timestamp,
	"status" "instance_status" DEFAULT 'pending' NOT NULL,
	"timeout_at" timestamp DEFAULT NOW() + interval '24 hours' NOT NULL,
	"stream_url" varchar(1024)
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "cyberdesk_instances" ADD CONSTRAINT "cyberdesk_instances_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE cascade ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
