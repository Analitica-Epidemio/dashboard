/**
 * Estrategias API Layer
 *
 * Semantic hooks for event classification strategies (estrategias).
 * Uses $api client internally - all types from OpenAPI schema.
 *
 * @module features/estrategias/api
 */

import { $api } from '@/lib/api/client';
import type { components, operations } from '@/lib/api/types';

// ============================================================================
// TYPES - Re-exported from OpenAPI schema
// ============================================================================

/**
 * Event classification strategy
 */
export type EventStrategy = components['schemas']['EstrategiaClasificacionResponse'];

/**
 * Strategy test response
 */
export type StrategyTestResponse = components['schemas']['StrategyTestResponse'];

/**
 * Audit log entry for strategy changes
 */
export type AuditLogResponse = components['schemas']['AuditLogResponse'];

/**
 * Filters for strategies list
 */
export type EstrategiasFilters = operations['list_strategies_api_v1_estrategias__get']['parameters']['query'];

// ============================================================================
// QUERY HOOKS - Semantic wrappers over $api
// ============================================================================

/**
 * Fetch event classification strategies list
 *
 * @param params - Filters (pagination, active_only, tipo_eno_id)
 * @returns Query with strategies list
 *
 * @example
 * ```tsx
 * const { data } = useEstrategias({ active_only: true, tipo_eno_id: 5 });
 * ```
 */
export function useEstrategias(params?: EstrategiasFilters) {
  return $api.useQuery('get', '/api/v1/estrategias/', {
    params: {
      query: params || {}
    }
  });
}

/**
 * Fetch single event classification strategy by ID
 *
 * @param strategyId - Strategy ID
 * @returns Query with strategy details
 *
 * @example
 * ```tsx
 * const { data } = useEstrategia(5);
 * ```
 */
export function useEstrategia(strategyId: number | null) {
  return $api.useQuery(
    'get',
    '/api/v1/estrategias/{strategy_id}',
    {
      params: {
        path: {
          strategy_id: strategyId!
        }
      }
    },
    {
      enabled: !!strategyId
    }
  );
}

// ============================================================================
// MUTATION HOOKS - Create, Update, Delete operations
// ============================================================================

/**
 * Create new event classification strategy
 *
 * @returns Mutation to create strategy
 *
 * @example
 * ```tsx
 * const createStrategy = useCrearEstrategia();
 * await createStrategy.mutateAsync({
 *   body: { tipo_eno_id: 5, rules: [...], priority: 1 }
 * });
 * ```
 */
export function useCrearEstrategia() {
  return $api.useMutation('post', '/api/v1/estrategias/');
}

/**
 * Update existing event classification strategy
 *
 * @returns Mutation to update strategy
 *
 * @example
 * ```tsx
 * const updateStrategy = useActualizarEstrategia();
 * await updateStrategy.mutateAsync({
 *   params: { path: { strategy_id: 5 } },
 *   body: { rules: [...], priority: 2 }
 * });
 * ```
 */
export function useActualizarEstrategia() {
  return $api.useMutation('put', '/api/v1/estrategias/{strategy_id}');
}

/**
 * Delete event classification strategy
 *
 * @returns Mutation to delete strategy
 *
 * @example
 * ```tsx
 * const deleteStrategy = useEliminarEstrategia();
 * await deleteStrategy.mutateAsync({
 *   params: { path: { strategy_id: 5 } }
 * });
 * ```
 */
export function useEliminarEstrategia() {
  return $api.useMutation('delete', '/api/v1/estrategias/{strategy_id}');
}

/**
 * Activate event classification strategy
 *
 * Sets a strategy as active for its event type.
 * Only one strategy can be active per event type.
 *
 * @returns Mutation to activate strategy
 *
 * @example
 * ```tsx
 * const activateStrategy = useActivarEstrategia();
 * await activateStrategy.mutateAsync({
 *   params: { path: { strategy_id: 5 } }
 * });
 * ```
 */
export function useActivarEstrategia() {
  return $api.useMutation('post', '/api/v1/estrategias/{strategy_id}/activate');
}

/**
 * Test event classification strategy
 *
 * Tests the strategy rules against sample data to preview results.
 *
 * @returns Mutation to test strategy
 *
 * @example
 * ```tsx
 * const testStrategy = useProbarEstrategia();
 * await testStrategy.mutateAsync({
 *   params: { path: { strategy_id: 5 } },
 *   body: { test_data: {...} }
 * });
 * ```
 */
export function useProbarEstrategia() {
  return $api.useMutation('post', '/api/v1/estrategias/{strategy_id}/test');
}
