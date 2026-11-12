/**
 * Supabase Cloud Infrastructure Integration for FRS V7.1 K2 Admin Console
 * Provides configuration and REST/Auth request wrappers.
 */

export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  process.env.SUPABASE_URL ||
  "https://hzqbgkdhxcnyakjjbjas.supabase.co";

export const SUPABASE_PUBLISHABLE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
  process.env.SUPABASE_KEY ||
  "sb_publishable_-7c2WIgh_dbXIewd-7-BAA_EDWdSiqZ";

/**
 * Server-only service role key for Server Components and SSR when querying PostgREST directly.
 * Guarded by `typeof window === "undefined"` so it is never exposed to browser bundles.
 */
function getServerServiceRoleKey(): string | null {
  if (typeof window === "undefined") {
    return (
      process.env.SUPABASE_SERVICE_ROLE_KEY ||
      process.env.SUPABASE_SECRET_KEY ||
      null
    );
  }
  return null;
}

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
 * Employs server-side service-role elevation strictly within Server Components to query live Postgres.
 */
export async function supabaseFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const cleanBase = SUPABASE_URL.replace(/\/$/, "");
  const cleanEndpoint = endpoint.replace(/^\//, "");
  const targetUrl = `${cleanBase}/${cleanEndpoint}`;

  const serverKey = getServerServiceRoleKey();
  const activeKey = serverKey || SUPABASE_PUBLISHABLE_KEY;

  const headers = new Headers(options.headers || {});
  headers.set("apikey", activeKey);
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${activeKey}`);
  }

  return fetch(targetUrl, {
    ...options,
    headers,
  });
}
