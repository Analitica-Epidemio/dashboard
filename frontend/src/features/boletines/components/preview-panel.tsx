"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { BoletinSemanalTemplate } from "./types";
import { SECCIONES_METADATA } from "./types";

interface PreviewPanelProps {
  template: BoletinSemanalTemplate;
}

export function PreviewPanel({ template }: PreviewPanelProps) {
  const seccionesActivas = template.secciones.filter((s) => s.enabled);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-lg">Vista Previa de Estructura</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-2">
            {/* Portada preview */}
            <div className="border-l-4 border-blue-500 pl-4 py-3 bg-blue-50/50">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">📄</span>
                <span className="font-bold">PORTADA</span>
              </div>
              <div className="text-sm text-muted-foreground space-y-1">
                <div>{template.portada.titulo}</div>
                {template.portada.subtitulo && (
                  <div className="text-xs">{template.portada.subtitulo}</div>
                )}
                {template.portada.incluir_logo && (
                  <Badge variant="secondary" className="text-xs">Logo incluido</Badge>
                )}
                {template.portada.incluir_texto_estandar && (
                  <Badge variant="secondary" className="text-xs">Texto estándar</Badge>
                )}
              </div>
            </div>

            {/* Secciones activas */}
            {seccionesActivas.map((seccion) => {
              const metadata = SECCIONES_METADATA.find((m) => m.tipo === seccion.tipo);
              return (
                <div
                  key={seccion.id}
                  className={`border-l-4 pl-4 py-2 ${
                    metadata?.requiere_backend
                      ? "border-purple-500 bg-purple-50/50"
                      : "border-gray-300 bg-gray-50/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs font-mono w-8 justify-center">
                      {seccion.orden}
                    </Badge>
                    <span className="text-lg">{metadata?.icono}</span>
                    <span className="font-medium text-sm">{seccion.titulo}</span>
                  </div>
                  {metadata?.requiere_backend && (
                    <div className="text-xs text-muted-foreground ml-12 mt-1">
                      Generará datos automáticamente
                    </div>
                  )}
                </div>
              );
            })}

            {seccionesActivas.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <p>No hay secciones activas</p>
                <p className="text-xs mt-2">Activa al menos una sección para ver el preview</p>
              </div>
            )}
          </div>

          {/* Resumen al final */}
          <div className="mt-6 pt-4 border-t space-y-2">
            <h4 className="font-medium text-sm">Resumen</h4>
            <div className="text-xs text-muted-foreground space-y-1">
              <div>
                📄 {seccionesActivas.length} secciones activas de {template.secciones.length}{" "}
                totales
              </div>
              <div>
                🔢{" "}
                {seccionesActivas.filter((s) => {
                  const meta = SECCIONES_METADATA.find((m) => m.tipo === s.tipo);
                  return meta?.requiere_backend;
                }).length}{" "}
                secciones generarán datos automáticamente
              </div>
              <div>
                ✏️{" "}
                {seccionesActivas.filter((s) => {
                  const meta = SECCIONES_METADATA.find((m) => m.tipo === s.tipo);
                  return !meta?.requiere_backend;
                }).length}{" "}
                secciones son texto fijo/editable
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
