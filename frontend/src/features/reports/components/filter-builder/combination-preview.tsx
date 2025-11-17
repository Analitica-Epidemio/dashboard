'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Eye, AlertCircle, Check } from 'lucide-react'
import { ClassificationBadges, TipoClasificacion } from "@/components/selectors/classification-selector"

interface CombinationPreviewProps {
  groupName?: string
  eventIds: number[]
  eventNames?: string[]
  clasificaciones?: TipoClasificacion[]
  label?: string
  isValid: boolean
}

export function CombinationPreview({
  groupName,
  eventIds,
  eventNames,
  clasificaciones,
  label,
  isValid,
}: CombinationPreviewProps) {
  // No mostrar preview si no hay grupo seleccionado
  if (!groupName) {
    return (
      <Card className="border-2 border-dashed border-gray-300 bg-gray-50">
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Eye className="h-10 w-10 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-500">
              Vista previa aparecerá aquí
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={`border-2 transition-all ${
      isValid
        ? 'border-green-300 bg-green-50/30'
        : 'border-yellow-300 bg-yellow-50/30'
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Eye className="h-4 w-4" />
            Vista Previa
          </CardTitle>
          {isValid ? (
            <Badge className="bg-green-600 text-white">
              <Check className="h-3 w-3 mr-1" />
              Lista
            </Badge>
          ) : (
            <Badge variant="outline" className="border-yellow-600 text-yellow-700">
              <AlertCircle className="h-3 w-3 mr-1" />
              Incompleta
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Label personalizado */}
        {label && (
          <div className="pb-2 border-b">
            <p className="text-xs text-gray-500 mb-1">Etiqueta</p>
            <p className="text-sm font-semibold text-gray-900">{label}</p>
          </div>
        )}

        {/* Grupo */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Grupo de Eventos</p>
          <Badge variant="outline" className="font-medium">
            {groupName}
          </Badge>
        </div>

        {/* Eventos */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Eventos</p>
          {eventIds.length === 0 ? (
            <p className="text-sm text-gray-700">Todos los eventos del grupo</p>
          ) : (
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-900">
                {eventIds.length === 1
                  ? '1 evento seleccionado'
                  : `${eventIds.length} eventos seleccionados`}
              </p>
              {eventNames && eventNames.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {eventNames.slice(0, 3).map((name, i) => (
                    <span key={i} className="text-xs text-gray-600 bg-white px-2 py-0.5 rounded border">
                      {name}
                    </span>
                  ))}
                  {eventNames.length > 3 && (
                    <span className="text-xs text-gray-500 px-2 py-0.5">
                      +{eventNames.length - 3} más
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Clasificaciones */}
        {clasificaciones && clasificaciones.length > 0 && (
          <div>
            <p className="text-xs text-gray-500 mb-1">Clasificaciones</p>
            <ClassificationBadges classifications={clasificaciones} />
          </div>
        )}

        {!isValid && (
          <div className="pt-2 mt-2 border-t border-yellow-200">
            <p className="text-xs text-yellow-700 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              Selecciona un grupo para continuar
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
