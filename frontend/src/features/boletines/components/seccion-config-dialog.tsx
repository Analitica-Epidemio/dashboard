"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { SeccionConfig, TablaEnosParams, VigilanciaIRAParams, CapacidadHospitalariaParams, VigilanciaVirusParams, IntoxicacionCOParams, DiarreasParams, SUHParams } from "./types";
import { SECCIONES_METADATA } from "./types";
import { TablaEnosConfig } from "./configs/tabla-enos-config";
import { VigilanciaIRAConfig } from "./configs/vigilancia-ira-config";
import { CapacidadHospitalariaConfig } from "./configs/capacidad-hospitalaria-config";
import { VigilanciaVirusConfig } from "./configs/vigilancia-virus-config";
import { IntoxicacionCOConfig } from "./configs/intoxicacion-co-config";
import { DiarreasConfig } from "./configs/diarreas-config";
import { SUHConfig } from "./configs/suh-config";

interface SeccionConfigDialogProps {
  seccion: SeccionConfig;
  onSave: (seccion: SeccionConfig) => void;
  onCancel: () => void;
}

export function SeccionConfigDialog({
  seccion,
  onSave,
  onCancel,
}: SeccionConfigDialogProps) {
  const [editedSeccion, setEditedSeccion] = useState<SeccionConfig>(seccion);

  const metadata = SECCIONES_METADATA.find((m) => m.tipo === seccion.tipo);

  const handleParamsChange = (params: Record<string, unknown>) => {
    setEditedSeccion((prev) => ({ ...prev, params }));
  };

  const handleSave = () => {
    onSave(editedSeccion);
  };

  // Renderizar configuración específica según tipo de sección
  const renderConfigComponent = () => {
    switch (seccion.tipo) {
      case "tabla_enos":
        return (
          <TablaEnosConfig
            params={(editedSeccion.params || {}) as TablaEnosParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "vigilancia_ira":
        return (
          <VigilanciaIRAConfig
            params={(editedSeccion.params || {}) as VigilanciaIRAParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "capacidad_hospitalaria":
        return (
          <CapacidadHospitalariaConfig
            params={(editedSeccion.params || {}) as CapacidadHospitalariaParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "vigilancia_virus":
        return (
          <VigilanciaVirusConfig
            params={(editedSeccion.params || {}) as VigilanciaVirusParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "intoxicacion_co":
        return (
          <IntoxicacionCOConfig
            params={(editedSeccion.params || {}) as IntoxicacionCOParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "diarreas":
        return (
          <DiarreasConfig
            params={(editedSeccion.params || {}) as DiarreasParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      case "suh":
        return (
          <SUHConfig
            params={(editedSeccion.params || {}) as SUHParams}
            onChange={(p) => handleParamsChange(p as Record<string, unknown>)}
          />
        );
      default:
        return (
          <div className="py-8 text-center text-muted-foreground">
            <p>Esta sección no tiene opciones de configuración.</p>
            <p className="text-sm mt-2">
              Los datos se generarán automáticamente al crear el boletín.
            </p>
          </div>
        );
    }
  };

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-2xl">{metadata?.icono}</span>
            <div>
              <div>Configurar: {seccion.titulo}</div>
              <p className="text-sm font-normal text-muted-foreground mt-1">
                {metadata?.descripcion}
              </p>
            </div>
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4 py-4">{renderConfigComponent()}</div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>Guardar Configuración</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
