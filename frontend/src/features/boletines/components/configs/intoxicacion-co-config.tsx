"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import type { IntoxicacionCOParams } from "../types";

interface IntoxicacionCOConfigProps {
  params: IntoxicacionCOParams;
  onChange: (params: IntoxicacionCOParams) => void;
}

export function IntoxicacionCOConfig({ params, onChange }: IntoxicacionCOConfigProps) {
  const updateField = <K extends keyof IntoxicacionCOParams>(
    field: K,
    value: IntoxicacionCOParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between space-x-2 py-2 border-b">
        <div className="space-y-0.5">
          <Label>Gráfico por UGD</Label>
          <p className="text-xs text-muted-foreground">
            Casos por Unidad de Gestión Descentralizada
          </p>
        </div>
        <Switch
          checked={params.incluir_grafico_ugd}
          onCheckedChange={(checked) => updateField("incluir_grafico_ugd", checked)}
        />
      </div>

      <div className="flex items-center justify-between space-x-2 py-2 border-b">
        <div className="space-y-0.5">
          <Label>Comparar con año anterior</Label>
          <p className="text-xs text-muted-foreground">
            Muestra comparación con el año configurado abajo
          </p>
        </div>
        <Switch
          checked={params.comparar_con_año_anterior}
          onCheckedChange={(checked) =>
            updateField("comparar_con_año_anterior", checked)
          }
        />
      </div>

      {params.comparar_con_año_anterior && (
        <div>
          <Label>Año de comparación</Label>
          <Input
            type="number"
            min={2000}
            max={2099}
            value={params.año_comparacion}
            onChange={(e) =>
              updateField("año_comparacion", parseInt(e.target.value) || new Date().getFullYear() - 1)
            }
            className="mt-2"
          />
        </div>
      )}
    </div>
  );
}
