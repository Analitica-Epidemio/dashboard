"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import type { VigilanciaVirusParams } from "../types";

interface VigilanciaVirusConfigProps {
  params: VigilanciaVirusParams;
  onChange: (params: VigilanciaVirusParams) => void;
}

export function VigilanciaVirusConfig({ params, onChange }: VigilanciaVirusConfigProps) {
  const updateField = <K extends keyof VigilanciaVirusParams>(
    field: K,
    value: VigilanciaVirusParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Gráfico temporal por agente viral</Label>
            <p className="text-xs text-muted-foreground">
              Evolución semanal de VSR, Influenza A, SARS-CoV-2, etc.
            </p>
          </div>
          <Switch
            checked={params.incluir_grafico_temporal}
            onCheckedChange={(checked) => updateField("incluir_grafico_temporal", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Gráfico por grupos de edad</Label>
            <p className="text-xs text-muted-foreground">
              Distribución de agentes virales por edad
            </p>
          </div>
          <Switch
            checked={params.incluir_grafico_edad}
            onCheckedChange={(checked) => updateField("incluir_grafico_edad", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Tabla de casos de Influenza</Label>
            <p className="text-xs text-muted-foreground">
              Detalle de casos positivos de Influenza A/B
            </p>
          </div>
          <Switch
            checked={params.incluir_tabla_influenza}
            onCheckedChange={(checked) => updateField("incluir_tabla_influenza", checked)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-4 border-t">
        <div>
          <Label>Desde SE</Label>
          <Input
            type="number"
            min={1}
            max={53}
            value={params.periodo_desde_se}
            onChange={(e) =>
              updateField("periodo_desde_se", parseInt(e.target.value) || 1)
            }
            className="mt-2"
          />
        </div>
        <div>
          <Label>Hasta SE</Label>
          <Input
            type="number"
            min={1}
            max={53}
            value={params.periodo_hasta_se}
            onChange={(e) =>
              updateField("periodo_hasta_se", parseInt(e.target.value) || 39)
            }
            className="mt-2"
          />
        </div>
      </div>
    </div>
  );
}
