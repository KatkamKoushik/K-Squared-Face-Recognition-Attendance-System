/**
 * Supabase Cloud Infrastructure Integration for FRS V7.1 K² Admin Console
 * Provides configuration and REST/Auth request wrappers.
 */

export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  "https://hzqbgkdhxcnyakjjbjas.supabase.co";

export const SUPABASE_PUBLISHABLE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  "sb_publishable_-7c2WIgh_dbXIewd-7-BAA_EDWdSiqZ";

export interface SupabaseConfig {
  url: string;
  publishableKey: string;
  isConfigured: boolean;
}

/**
 * Returns active Supabase client configuration.
 */
export function getSupabaseConfig(): SupabaseConfig {
  return {
    url: SUPABASE_URL,
    publishableKey: SUPABASE_PUBLISHABLE_KEY,
    isConfigured: Boolean(SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY),
  };
}

/**
 * Isomorphic fetch wrapper for Supabase PostgREST & Auth endpoints.
 */
export async function supabaseFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const cleanBase = SUPABASE_URL.replace(/\/$/, "");
  const cleanEndpoint = endpoint.replace(/^\//, "");
  const targetUrl = `${cleanBase}/${cleanEndpoint}`;

  const headers = new Headers(options.headers || {});
  headers.set("apikey", SUPABASE_PUBLISHABLE_KEY);
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${SUPABASE_PUBLISHABLE_KEY}`);
  }

  return fetch(targetUrl, {
    ...options,
    headers,
  });
}
