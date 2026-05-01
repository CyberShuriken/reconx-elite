export const isSupabaseEnabled = Boolean(
  process.env.VITE_SUPABASE_URL && process.env.VITE_SUPABASE_PUBLISHABLE_KEY,
);

