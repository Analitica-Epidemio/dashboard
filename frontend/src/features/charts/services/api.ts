/**
 * API hooks para la nueva arquitectura Browse-First de charts
 */

/**
 * Función para ejecutar un chart (no hook, se usa directamente)
 */
export async function executeChart(request: {
  chart_codigo: string
  filtros?: Record<string, any>
  parametros?: Record<string, any>
  usar_cache?: boolean
}) {
  const response = await fetch('/api/v1/charts/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chart_codigo: request.chart_codigo,
      filtros: request.filtros || {},
      parametros: request.parametros || {},
      usar_cache: request.usar_cache ?? true,
      formato_respuesta: 'json'
    })
  })

  if (!response.ok) {
    throw new Error(`Error ejecutando chart: ${response.statusText}`)
  }

  return response.json()
}