"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import type { DiarreasParams } from "../types";

interface DiarreasConfigProps {
  params: DiarreasParams;
  onChange: (params: DiarreasParams) => void;
}

export function DiarreasConfig({ params, onChange }: DiarreasConfigProps) {
  const updateField = <K extends keyof DiarreasParams>(
    field: K,
    value: DiarreasParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Corredor endémico</Label>
            <p className="text-xs text-muted-foreground">
              Corredor endémico semanal de diarrea
            </p>
          </div>
          <Switch
            checked={params.incluir_corredor}
            onCheckedChange={(checked) => updateField("incluir_corredor", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Tabla de agentes etiológicos</Label>
            <p className="text-xs text-muted-foreground">
              Muestras procesadas y agentes detectados
            </p>
          </div>
          <Switch
            checked={params.incluir_tabla_agentes}
            onCheckedChange={(checked) => updateField("incluir_tabla_agentes", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Gráfico de distribución temporal</Label>
            <p className="text-xs text-muted-foreground">
              Distribución de agentes por semana epidemiológica
            </p>
          </div>
          <Switch
            checked={params.incluir_grafico_distribucion}
            onCheckedChange={(checked) =>
              updateField("incluir_grafico_distribucion", checked)
            }
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
              updateField("periodo_hasta_se", parseInt(e.target.value) || 38)
            }
            className="mt-2"
          />
        </div>
      </div>
    </div>
  );
}
