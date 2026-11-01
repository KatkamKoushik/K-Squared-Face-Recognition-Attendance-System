/**
 * Safe Administrative Session Management & Storage Sanitization.
 * Conforms to Checklist Controls 15-B003, 15-B008, and 19-B002.
 */

const TOKEN_KEY = "frs_admin_access_token";
const USER_KEY = "frs_admin_user_profile";
const DIRECTORY_CACHE_KEY = "frs_admin_student_directory_cache";

export function getStoredAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

export function setStoredAdminToken(token: string, persist: boolean = false): void {
  if (typeof window === "undefined") return;
  if (persist) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * Completely purges all administrative tokens, cached rosters, and student
 * directory records from both localStorage and sessionStorage on logout.
 */
export function purgeAdminSession(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(DIRECTORY_CACHE_KEY);

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(DIRECTORY_CACHE_KEY);

    // Broadcast logout event across browser context
    window.dispatchEvent(new Event("frs:admin:logout"));
  } catch (err) {
    console.error("Failed to purge session storage completely:", err);
  }
}
