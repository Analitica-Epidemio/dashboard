/**
 * Tipos de respuesta de la API siguiendo mejores prácticas.
 * 
 * Basado en el patrón usado por Stripe, GitHub, etc:
 * - Éxitos: HTTP 2xx con { data: T }
 * - Errores: HTTP 4xx/5xx con { error: ErrorDetail }
 */

/**
 * Detalle de un error de la API
 */
export interface ErrorDetail {
  code: string;      // Código machine-readable (ej: "USER_NOT_FOUND")
  message: string;   // Mensaje human-readable
  field?: string;    // Campo que causó el error (opcional)
}

/**
 * Respuesta de error de la API
 * Se recibe con códigos HTTP 4xx/5xx
 */
export interface ErrorResponse {
  error: ErrorDetail;
  errors?: ErrorDetail[];  // Errores adicionales (validación múltiple)
  request_id?: string;     // ID para tracking
}

/**
 * Respuesta exitosa de la API
 * Se recibe con códigos HTTP 2xx
 */
export interface SuccessResponse<T> {
  data: T;
  meta?: Record<string, any>;  // Metadata opcional
}

/**
 * Respuesta paginada
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  links?: {
    first?: string;
    prev?: string;
    next?: string;
    last?: string;
  };
}

/**
 * Type guard para verificar si es un error
 */
export function isErrorResponse(response: any): response is ErrorResponse {
  return response && typeof response === 'object' && 'error' in response;
}

/**
 * Type guard para verificar si es éxito
 */
export function isSuccessResponse<T>(response: any): response is SuccessResponse<T> {
  return response && typeof response === 'object' && 'data' in response;
}