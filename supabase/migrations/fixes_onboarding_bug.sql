-- 🔥 FIX 1 & 2: REMOVE DEFAULTS & ENABLE RLS (NUCLEAR OPTION)

-- 1. Remove dangerous default (Treat it like a fuse)
ALTER TABLE public.profiles 
ALTER COLUMN onboarding_completed DROP DEFAULT; 
-- Note: If column is NOT NULL, this forces the Trigger to handle it explicitly.

-- 2. FIX TRIGGER (The only place creating the row)
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, onboarding_completed, email)
  values (new.id, false, new.email);  -- Explicit FALSE
  return new;
end;
$$ language plpgsql security definer;

-- Re-apply trigger
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- 3. RLS POLICIES (MANDATORY for Client Update)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Allow users to UPDATE their own onboarding state (Critical)
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" 
ON public.profiles FOR UPDATE 
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Allow users to SELECT their own profile (Critical for Route Guards)
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" 
ON public.profiles FOR SELECT 
USING (auth.uid() = id);

-- Allow users to INSERT their own profile (Backup safety)
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" 
ON public.profiles FOR INSERT 
WITH CHECK (auth.uid() = id);

-- 4. CLEANUP (Optional)
-- UPDATE public.profiles SET onboarding_completed = false WHERE onboarding_completed IS NULL;
