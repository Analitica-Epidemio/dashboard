/**
 * User and session management hooks using OpenAPI-generated types
 */

import { $api } from "../client";

/**
 * Get current user profile
 */
export function useUserProfile() {
  return $api.useQuery("get", "/api/v1/auth/me");
}

/**
 * Update user profile
 */
export function useUpdateProfile() {
  return $api.useMutation("put", "/api/v1/auth/me");
}

/**
 * Change password
 */
export function useChangePassword() {
  return $api.useMutation("post", "/api/v1/auth/change-password");
}

/**
 * Get user sessions
 */
export function useUserSessions() {
  return $api.useQuery("get", "/api/v1/auth/sessions");
}

/**
 * Logout specific session
 */
export function useLogoutSession() {
  return $api.useMutation("delete", "/api/v1/auth/sessions/{session_id}");
}

/**
 * Logout all sessions
 */
export function useLogoutAllSessions() {
  return $api.useMutation("post", "/api/v1/auth/logout-all");
}
