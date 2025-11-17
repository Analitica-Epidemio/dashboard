/**
 * Auth API Layer
 *
 * Semantic hooks for authentication and user management endpoints.
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/auth/api
 */

import { $api } from "@/lib/api/client";

// ============================================================================
// QUERY HOOKS - User data
// ============================================================================

/**
 * Get current authenticated user profile
 *
 * Returns the profile information for the currently logged-in user.
 *
 * @returns Query with user profile data
 *
 * @example
 * ```tsx
 * const { data } = useUserProfile();
 * console.log(data?.data?.email);
 * ```
 */
export function useUserProfile() {
  return $api.useQuery("get", "/api/v1/auth/me");
}

/**
 * Get active user sessions
 *
 * Returns all active sessions for the current user across different devices.
 *
 * @returns Query with user sessions list
 *
 * @example
 * ```tsx
 * const { data } = useUserSessions();
 * ```
 */
export function useUserSessions() {
  return $api.useQuery("get", "/api/v1/auth/sessions");
}

// ============================================================================
// MUTATION HOOKS - User management
// ============================================================================

/**
 * Update current user profile
 *
 * Updates profile information for the authenticated user.
 *
 * @returns Mutation to update profile
 *
 * @example
 * ```tsx
 * const updateProfile = useUpdateProfile();
 * await updateProfile.mutateAsync({
 *   body: { nombre: 'Juan', apellido: 'Pérez' }
 * });
 * ```
 */
export function useUpdateProfile() {
  return $api.useMutation("put", "/api/v1/auth/me");
}

/**
 * Change user password
 *
 * Changes the password for the authenticated user.
 * Requires current password for verification.
 *
 * @returns Mutation to change password
 *
 * @example
 * ```tsx
 * const changePassword = useChangePassword();
 * await changePassword.mutateAsync({
 *   body: {
 *     current_password: 'old_pass',
 *     new_password: 'new_pass'
 *   }
 * });
 * ```
 */
export function useChangePassword() {
  return $api.useMutation("post", "/api/v1/auth/change-password");
}

/**
 * Logout specific session
 *
 * Terminates a specific user session by ID.
 *
 * @returns Mutation to logout session
 *
 * @example
 * ```tsx
 * const logoutSession = useLogoutSession();
 * await logoutSession.mutateAsync({
 *   params: { path: { session_id: '123' } }
 * });
 * ```
 */
export function useLogoutSession() {
  return $api.useMutation("delete", "/api/v1/auth/sessions/{session_id}");
}

/**
 * Logout all sessions
 *
 * Terminates all active sessions for the current user except the current one.
 *
 * @returns Mutation to logout all sessions
 *
 * @example
 * ```tsx
 * const logoutAll = useLogoutAllSessions();
 * await logoutAll.mutateAsync({ body: {} });
 * ```
 */
export function useLogoutAllSessions() {
  return $api.useMutation("post", "/api/v1/auth/logout-all");
}
