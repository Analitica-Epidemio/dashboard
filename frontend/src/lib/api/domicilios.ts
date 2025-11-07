/**
 * Domicilios API hooks and utilities
 * Uses the typed $api client for all requests
 */

import { $api } from "@/lib/api/client";
import type { operations, components } from "@/lib/api/types";

/**
 * Domicilio filters - extracted from API types
 */
export type DomicilioFilters =
  operations["list_domicilios_api_v1_domicilios_get"]["parameters"]["query"];

/**
 * Domicilio list item - extracted from API types
 */
export type DomicilioListItem = components["schemas"]["DomicilioListItem"];

/**
 * Domicilios list response - extracted from API types
 */
export type DomiciliosListResponse =
  components["schemas"]["DomiciliosListResponse"];

/**
 * Hook to fetch domicilios list with filters
 */
export function useDomicilios(params?: DomicilioFilters) {
  return $api.useQuery("get", "/api/v1/domicilios", {
    params: {
      query: params,
    },
  });
}
