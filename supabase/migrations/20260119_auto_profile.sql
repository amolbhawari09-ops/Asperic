-- STEP 3: AUTO-CREATE PROFILE ROW (MANDATORY)
-- Run this in Supabase SQL Editor to ensure every new user gets a profile row immediately.

-- Function to handle new user insertion
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, onboarding_completed)
  values (new.id, false);
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to execute function on new auth.users creation
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();
