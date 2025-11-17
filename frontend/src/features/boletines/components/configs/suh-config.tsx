"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import type { SUHParams } from "../types";

interface SUHConfigProps {
  params: SUHParams;
  onChange: (params: SUHParams) => void;
}

export function SUHConfig({ params, onChange }: SUHConfigProps) {
  const updateField = <K extends keyof SUHParams>(
    field: K,
    value: SUHParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Gráfico histórico</Label>
            <p className="text-xs text-muted-foreground">
              Distribución de casos de SUH desde 2014
            </p>
          </div>
          <Switch
            checked={params.incluir_grafico_historico}
            onCheckedChange={(checked) => updateField("incluir_grafico_historico", checked)}
          />
        </div>

        {params.incluir_grafico_historico && (
          <div>
            <Label>Año inicio del histórico</Label>
            <Input
              type="number"
              min={2000}
              max={2099}
              value={params.año_inicio_historico}
              onChange={(e) =>
                updateField("año_inicio_historico", parseInt(e.target.value) || 2014)
              }
              className="mt-2"
            />
          </div>
        )}

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label>Tabla de casos detallados</Label>
            <p className="text-xs text-muted-foreground">
              Tabla con descripción de cada caso confirmado
            </p>
          </div>
          <Switch
            checked={params.incluir_tabla_casos}
            onCheckedChange={(checked) => updateField("incluir_tabla_casos", checked)}
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
