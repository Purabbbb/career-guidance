import { createClient } from '@supabase/supabase-js'

const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_URL ||
  process.env.NEXT_PUBLIC_SUPABASE_URL

const supabaseKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

const isConfigured = Boolean(supabaseUrl && supabaseKey)

if (!isConfigured) {
  console.warn('Supabase env vars missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env')
}

// Fallback to dummy credentials so createClient does not crash the app before React renders
export const supabase = createClient(
  supabaseUrl || 'https://placeholder-project.supabase.co',
  supabaseKey || 'placeholder-anon-key-prevent-crash'
)

export const isSupabaseConfigured = isConfigured