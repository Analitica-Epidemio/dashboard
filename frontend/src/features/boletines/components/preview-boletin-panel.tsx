"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { BoletinSemanalTemplate } from "./types";

interface PreviewBoletinPanelProps {
  template: BoletinSemanalTemplate;
}

export function PreviewBoletinPanel({ template }: PreviewBoletinPanelProps) {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          👁️ Preview del Boletín
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Vista previa del contenido renderizado
        </p>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-6">
            {/* Portada */}
            <div className="border-l-4 border-blue-500 pl-4 py-4 bg-blue-50/50">
              <div className="text-2xl font-bold text-blue-900">
                {template.portada.titulo}
              </div>
              {template.portada.subtitulo && (
                <div className="text-lg text-blue-700 mt-1">
                  {template.portada.subtitulo}
                </div>
              )}
              {template.portada.incluir_logo && (
                <Badge variant="secondary" className="mt-2">
                  🏛️ Logo institucional
                </Badge>
              )}
            </div>

            {/* Secciones */}
            {template.secciones.map((seccion) => (
              <div
                key={seccion.id}
                className="border-l-4 border-gray-300 pl-4 py-3 bg-gray-50/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline" className="text-xs font-mono">
                    #{seccion.orden}
                  </Badge>
                  <h3 className="font-semibold text-gray-900">
                    {seccion.titulo}
                  </h3>
                </div>
                <div
                  className="prose prose-sm max-w-none text-gray-700"
                  dangerouslySetInnerHTML={{
                    __html: seccion.contenido_html,
                  }}
                />
              </div>
            ))}

            {template.secciones.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <p className="text-sm">No hay secciones para mostrar</p>
              </div>
            )}

            {/* Leyenda de variables */}
            <div className="border-t pt-4 mt-6">
              <h4 className="text-xs font-semibold text-muted-foreground mb-2">
                💡 Variables detectadas
              </h4>
              <div className="flex flex-wrap gap-2">
                {getAllVariables(template).map((variable) => (
                  <Badge
                    key={variable}
                    variant="secondary"
                    className="text-xs font-mono"
                  >
                    {variable}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Helper para extraer todas las variables usadas
function getAllVariables(template: BoletinSemanalTemplate): string[] {
  const variables = new Set<string>();
  const regex = /\{\{([^}]+)\}\}/g;

  template.secciones.forEach((seccion) => {
    let match;
    while ((match = regex.exec(seccion.contenido_html)) !== null) {
      variables.add(`{{${match[1]}}}`);
    }
  });

  return Array.from(variables);
}
