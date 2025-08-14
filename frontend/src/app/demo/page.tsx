"use client";

import { $api } from "@/lib/api/client";

export default function DemoPage() {
  const { data, error, isPending, refetch } = $api.useQuery(
    "get",
    "/api/v1/hello"
  );

  // Loading state con skeleton
  if (isPending) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-8"></div>
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="h-6 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="h-6 bg-gray-200 rounded w-full"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-8">
            API Demo - Error State
          </h1>
          
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Header con icono de error */}
            <div className="bg-red-50 border-b border-red-100 px-6 py-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h2 className="text-lg font-semibold text-red-900">
                  Error del Servidor
                </h2>
              </div>
            </div>
            
            {/* Contenido del error */}
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Código de error</p>
                <p className="font-mono text-sm bg-red-50 text-red-700 px-3 py-1 rounded inline-block">
                  {error.error.code}
                </p>
              </div>
              
              <div>
                <p className="text-sm text-gray-500 mb-1">Mensaje</p>
                <p className="text-gray-900">
                  {error.error.message}
                </p>
              </div>
              
              {error.request_id && (
                <div>
                  <p className="text-sm text-gray-500 mb-1">ID de solicitud</p>
                  <p className="font-mono text-xs text-gray-600">
                    {error.request_id}
                  </p>
                </div>
              )}
            </div>
            
            {/* Footer con botón de retry */}
            <div className="bg-gray-50 px-6 py-3 border-t">
              <button
                onClick={() => refetch()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reintentar
              </button>
            </div>
          </div>
          
          <p className="text-sm text-gray-500 mt-4 text-center">
            Tip: El endpoint tiene 50% de probabilidad de error para testing
          </p>
        </div>
      </div>
    );
  }

  // Success state
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-8">
          API Demo - Success State
        </h1>
        
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Header con icono de éxito */}
          <div className="bg-green-50 border-b border-green-100 px-6 py-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-lg font-semibold text-green-900">
                Respuesta Exitosa
              </h2>
            </div>
          </div>
          
          {/* Contenido de la respuesta */}
          <div className="p-6 space-y-4">
            <div>
              <p className="text-sm text-gray-500 mb-1">Mensaje</p>
              <p className="text-lg text-gray-900 font-medium">
                {data?.data.message}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 mb-1">Servidor</p>
              <p className="font-mono text-sm bg-gray-50 text-gray-700 px-3 py-1 rounded inline-block">
                {data?.data.server}
              </p>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 mb-1">Timestamp</p>
              <p className="text-gray-900">
                {data?.data.timestamp ? new Date(data.data.timestamp).toLocaleString('es-AR', {
                  dateStyle: 'medium',
                  timeStyle: 'medium'
                }) : '-'}
              </p>
            </div>
          </div>
          
          {/* Footer con botón de refresh */}
          <div className="bg-gray-50 px-6 py-3 border-t flex justify-between items-center">
            <span className="text-sm text-gray-500">
              Respuesta HTTP 200 OK
            </span>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Actualizar
            </button>
          </div>
        </div>
        
        <p className="text-sm text-gray-500 mt-4 text-center">
          Tip: El endpoint tiene 50% de probabilidad de error para testing
        </p>
      </div>
    </div>
  );
}