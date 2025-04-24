CREATE TABLE IF NOT EXISTS "desktop_instances" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"created_at" timestamp DEFAULT now(),
	"ended_at" timestamp
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "desktop_instances" ADD CONSTRAINT "desktop_instances_user_id_users_id_fk" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
