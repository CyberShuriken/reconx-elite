import { createClient } from "@supabase/supabase-js";

import { isSupabaseEnabled } from "./backendMode";

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const supabase = isSupabaseEnabled
  ? createClient(supabaseUrl, supabaseKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;

function requireSupabase() {
  if (!supabase) {
    throw new Error("Supabase is not configured");
  }
  return supabase;
}

function mapTargetRow(row) {
  return {
    id: row.id,
    domain: row.domain,
    notes: row.notes || "",
    created_at: row.created_at,
    scan_count: 0,
    latest_scan: null,
    scans: [],
  };
}

export async function signInWithPassword({ email, password }) {
  const client = requireSupabase();
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signUp({ email, password }) {
  const client = requireSupabase();
  const { data, error } = await client.auth.signUp({
    email,
    password,
    options: {
      data: { role: "user" },
    },
  });
  if (error) throw error;
  return data;
}

export async function signOut() {
  const client = requireSupabase();
  const { error } = await client.auth.signOut();
  if (error) throw error;
}

export async function listTargets() {
  const client = requireSupabase();
  const { data, error } = await client
    .from("targets")
    .select("id, domain, notes, created_at")
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data || []).map(mapTargetRow);
}

export async function createTarget(domain) {
  const client = requireSupabase();
  const {
    data: { user },
  } = await client.auth.getUser();
  const insertPayload = user ? { domain, user_id: user.id } : { domain };
  let { data, error } = await client
    .from("targets")
    .insert(insertPayload)
    .select("id, domain, notes, created_at")
    .single();
  if (error && user) {
    const fallback = await client
      .from("targets")
      .insert({ domain })
      .select("id, domain, notes, created_at")
      .single();
    data = fallback.data;
    error = fallback.error;
  }
  if (error) throw error;
  return mapTargetRow(data);
}

export async function getTargetById(targetId) {
  const client = requireSupabase();
  const { data, error } = await client
    .from("targets")
    .select("id, domain, notes, created_at")
    .eq("id", Number(targetId))
    .single();
  if (error) throw error;
  return mapTargetRow(data);
}

export async function updateTargetNotes(targetId, notes) {
  const client = requireSupabase();
  const { data, error } = await client
    .from("targets")
    .update({ notes })
    .eq("id", Number(targetId))
    .select("id, domain, notes, created_at")
    .single();
  if (error) throw error;
  return mapTargetRow(data);
}

export async function listNotifications() {
  const client = requireSupabase();
  const { data, error } = await client
    .from("notifications")
    .select("id, message, read, created_at")
    .order("created_at", { ascending: false })
    .limit(20);
  if (error) throw error;
  return data || [];
}
