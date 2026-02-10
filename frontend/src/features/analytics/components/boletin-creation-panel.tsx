"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import {
  FileText,
  Loader2,
  Pencil,
  ArrowLeft,
  Settings2,
  Eye,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { EventoSeleccionado } from "@/features/boletines/types";
import { SelectedEventsList } from "./selected-events-list";
import { QuickAddEvents } from "./quick-add-events";

const BoletinReadOnlyPreview = dynamic(
  () =>
    import("./boletin-readonly-preview").then((m) => ({
      default: m.BoletinReadOnlyPreview,
    })),
  { ssr: false }
);

interface BoletinCreationPanelProps {
  eventosSeleccionados: EventoSeleccionado[];
  semana: number;
  anio: number;
  numSemanas: number;
  tituloCustom: string;
  onEventosChange: (eventos: EventoSeleccionado[]) => void;
  onAddEvento: (evento: EventoSeleccionado) => void;
  onNumSemanasChange: (n: number) => void;
  onTituloChange: (t: string) => void;
  onPreview: () => void;
  isPreviewing: boolean;
  onEditInEditor: () => Promise<number | null>;
  isCreating: boolean;
  generatedContent: string | null;
}

export function BoletinCreationPanel({
  eventosSeleccionados,
  semana,
  anio,
  numSemanas,
  tituloCustom,
  onEventosChange,
  onAddEvento,
  onNumSemanasChange,
  onTituloChange,
  onPreview,
  isPreviewing,
  onEditInEditor,
  isCreating,
  generatedContent,
}: BoletinCreationPanelProps) {
  const router = useRouter();
  const [showPreview, setShowPreview] = useState(false);

  const hasPreview = showPreview && generatedContent;

  return (
    <div className="flex flex-col h-full bg-background border-l">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          {hasPreview ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2"
              onClick={() => setShowPreview(false)}
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Volver
            </Button>
          ) : (
            <>
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-semibold">Nuevo Boletín</span>
            </>
          )}
        </div>
        <Badge variant="outline" className="text-xs">
          SE {semana}/{anio}
        </Badge>
      </div>

      {hasPreview ? (
        /* ========== PREVIEW MODE ========== */
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="px-4 py-2 border-b space-y-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Eye className="h-3.5 w-3.5" />
              Vista previa (no guardada)
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                className="flex-1 gap-1.5"
                disabled={isCreating}
                onClick={async () => {
                  const instanceId = await onEditInEditor();
                  if (instanceId) {
                    router.push(
                      `/dashboard/boletines/instances/${instanceId}`
                    );
                  }
                }}
              >
                {isCreating ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Pencil className="h-3.5 w-3.5" />
                )}
                {isCreating ? "Creando..." : "Editar en editor"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5"
                onClick={() => setShowPreview(false)}
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Ajustar
              </Button>
            </div>
          </div>
          <BoletinReadOnlyPreview content={generatedContent} />
        </div>
      ) : (
        /* ========== CONFIG + LIVE DATA ========== */
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            {/* Selected events with live preview data */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  Eventos a incluir
                </Label>
                <Badge variant="secondary" className="text-[10px]">
                  {eventosSeleccionados.length}
                </Badge>
              </div>

              {eventosSeleccionados.length > 0 ? (
                <SelectedEventsList
                  eventos={eventosSeleccionados}
                  semana={semana}
                  anio={anio}
                  numSemanas={numSemanas}
                  onChange={onEventosChange}
                />
              ) : (
                <div className="text-center py-6 text-muted-foreground border border-dashed rounded-lg">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-40" />
                  <p className="text-xs">Sin eventos seleccionados</p>
                  <p className="text-[10px] mt-0.5">
                    Marcá checkboxes en las tablas de cambios o usá el botón de abajo
                  </p>
                </div>
              )}

              <div className="mt-2">
                <QuickAddEvents
                  eventosSeleccionados={eventosSeleccionados}
                  onAdd={onAddEvento}
                />
              </div>
            </div>

            <Separator />

            {/* Settings */}
            <div className="space-y-3">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                <Settings2 className="h-3.5 w-3.5" />
                Configuración
              </div>

              <div className="space-y-2">
                <div>
                  <Label htmlFor="titulo" className="text-xs">
                    Título (opcional)
                  </Label>
                  <Input
                    id="titulo"
                    value={tituloCustom}
                    onChange={(e) => onTituloChange(e.target.value)}
                    placeholder={`Boletín SE ${semana}/${anio}`}
                    className="h-8 text-xs mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="numSemanas" className="text-xs">
                    Semanas a comparar
                  </Label>
                  <Input
                    id="numSemanas"
                    type="number"
                    value={numSemanas}
                    onChange={(e) =>
                      onNumSemanasChange(parseInt(e.target.value) || 4)
                    }
                    min={1}
                    max={12}
                    className="h-8 text-xs mt-1 w-20"
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Action buttons */}
            <div className="space-y-2">
              <Button
                onClick={() => {
                  onPreview();
                  setShowPreview(true);
                }}
                disabled={isPreviewing}
                variant="outline"
                className="w-full gap-2"
              >
                {isPreviewing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generando vista previa...
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4" />
                    Vista previa
                  </>
                )}
              </Button>
            </div>
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
