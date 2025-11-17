"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import type { VigilanciaIRAParams } from "../types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";

interface VigilanciaIRAConfigProps {
  params: VigilanciaIRAParams;
  onChange: (params: VigilanciaIRAParams) => void;
}

export function VigilanciaIRAConfig({ params, onChange }: VigilanciaIRAConfigProps) {
  const updateField = <K extends keyof VigilanciaIRAParams>(
    field: K,
    value: VigilanciaIRAParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  const enfermedadesActivas = [
    params.incluir_eti,
    params.incluir_neumonia,
    params.incluir_bronquiolitis,
  ].filter(Boolean).length;

  return (
    <div className="space-y-6">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Esta sección genera corredores endémicos para infecciones respiratorias agudas. Los
          gráficos se crearán automáticamente con datos de la base de datos.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        <h4 className="font-medium text-sm">Enfermedades a incluir</h4>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_eti">ETI (Enfermedad Tipo Influenza)</Label>
            <p className="text-xs text-muted-foreground">
              Corredor endémico + análisis de zona epidémica
            </p>
          </div>
          <Switch
            id="incluir_eti"
            checked={params.incluir_eti}
            onCheckedChange={(checked) => updateField("incluir_eti", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_neumonia">Neumonía</Label>
            <p className="text-xs text-muted-foreground">
              Corredor endémico + análisis de zona epidémica
            </p>
          </div>
          <Switch
            id="incluir_neumonia"
            checked={params.incluir_neumonia}
            onCheckedChange={(checked) => updateField("incluir_neumonia", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2 border-b">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_bronquiolitis">Bronquiolitis</Label>
            <p className="text-xs text-muted-foreground">
              Corredor endémico + análisis de zona epidémica
            </p>
          </div>
          <Switch
            id="incluir_bronquiolitis"
            checked={params.incluir_bronquiolitis}
            onCheckedChange={(checked) => updateField("incluir_bronquiolitis", checked)}
          />
        </div>

        {enfermedadesActivas === 0 && (
          <Alert variant="destructive" className="bg-yellow-50 border-yellow-200">
            <AlertDescription className="text-yellow-800">
              ⚠️ Debes seleccionar al menos una enfermedad para incluir en esta sección.
            </AlertDescription>
          </Alert>
        )}
      </div>

      <div className="space-y-4 pt-4 border-t">
        <h4 className="font-medium text-sm">Gráficos adicionales</h4>

        <div className="flex items-center justify-between space-x-2 py-2">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_grafico_edad">
              Gráfico de distribución por edad
            </Label>
            <p className="text-xs text-muted-foreground">
              Muestra casos de ETI, Neumonía y Bronquiolitis por grupo etario
            </p>
          </div>
          <Switch
            id="incluir_grafico_edad"
            checked={params.incluir_grafico_edad}
            onCheckedChange={(checked) => updateField("incluir_grafico_edad", checked)}
          />
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t">
        <h4 className="font-medium text-sm">Período de análisis</h4>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="periodo_desde_se">Desde SE</Label>
            <Input
              id="periodo_desde_se"
              type="number"
              min={1}
              max={53}
              value={params.periodo_desde_se}
              onChange={(e) =>
                updateField("periodo_desde_se", parseInt(e.target.value) || 1)
              }
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">Semana epidemiológica inicio</p>
          </div>

          <div>
            <Label htmlFor="periodo_hasta_se">Hasta SE</Label>
            <Input
              id="periodo_hasta_se"
              type="number"
              min={1}
              max={53}
              value={params.periodo_hasta_se}
              onChange={(e) =>
                updateField("periodo_hasta_se", parseInt(e.target.value) || 38)
              }
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Usualmente la SE actual o anterior
            </p>
          </div>
        </div>

        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            El año se tomará automáticamente del boletín que estés generando. Estos valores
            son configurables al generar cada boletín.
          </AlertDescription>
        </Alert>
      </div>

      {/* Vista previa conceptual */}
      <div className="pt-4 border-t">
        <h4 className="font-medium text-sm mb-3">Contenido generado</h4>
        <div className="space-y-2 text-sm text-muted-foreground">
          {params.incluir_eti && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              <span>Corredor endémico de ETI (SE {params.periodo_desde_se}-{params.periodo_hasta_se})</span>
            </div>
          )}
          {params.incluir_neumonia && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span>Corredor endémico de Neumonía (SE {params.periodo_desde_se}-{params.periodo_hasta_se})</span>
            </div>
          )}
          {params.incluir_bronquiolitis && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-purple-500" />
              <span>Corredor endémico de Bronquiolitis (SE {params.periodo_desde_se}-{params.periodo_hasta_se})</span>
            </div>
          )}
          {params.incluir_grafico_edad && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-orange-500" />
              <span>Gráfico de distribución por grupo etario</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
