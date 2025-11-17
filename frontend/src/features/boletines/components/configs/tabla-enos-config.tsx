"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import type { TablaEnosParams } from "../types";
import { Card } from "@/components/ui/card";

interface TablaEnosConfigProps {
  params: TablaEnosParams;
  onChange: (params: TablaEnosParams) => void;
}

export function TablaEnosConfig({ params, onChange }: TablaEnosConfigProps) {
  const updateField = <K extends keyof TablaEnosParams>(
    field: K,
    value: TablaEnosParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="top_n">Cantidad de eventos a mostrar</Label>
          <Select
            value={params.top_n?.toString() || "all"}
            onValueChange={(value) =>
              updateField("top_n", value === "all" ? undefined : parseInt(value))
            }
          >
            <SelectTrigger id="top_n" className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">Top 3 eventos</SelectItem>
              <SelectItem value="5">Top 5 eventos</SelectItem>
              <SelectItem value="10">Top 10 eventos</SelectItem>
              <SelectItem value="all">Todos los eventos</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground mt-2">
            Muestra los N eventos más frecuentes del período.
          </p>
        </div>

        <div>
          <Label htmlFor="ultimas_n_semanas">Período de análisis</Label>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-sm text-muted-foreground">Últimas</span>
            <Input
              id="ultimas_n_semanas"
              type="number"
              min={1}
              max={52}
              value={params.ultimas_n_semanas}
              onChange={(e) =>
                updateField("ultimas_n_semanas", parseInt(e.target.value) || 4)
              }
              className="w-20 text-center"
            />
            <span className="text-sm text-muted-foreground">semanas</span>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Se contarán hacia atrás desde la semana del boletín.
          </p>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t">
        <h4 className="font-medium text-sm">Filtros</h4>

        <div className="flex items-center justify-between space-x-2 py-2">
          <div className="space-y-0.5">
            <Label htmlFor="excluir_respiratorios">Excluir eventos respiratorios</Label>
            <p className="text-xs text-muted-foreground">
              Los eventos respiratorios se muestran en la sección de IRA
            </p>
          </div>
          <Switch
            id="excluir_respiratorios"
            checked={params.excluir_respiratorios}
            onCheckedChange={(checked) => updateField("excluir_respiratorios", checked)}
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-2">
          <div className="space-y-0.5">
            <Label htmlFor="solo_confirmados">Solo casos confirmados</Label>
            <p className="text-xs text-muted-foreground">
              Excluye casos sospechosos/probables
            </p>
          </div>
          <Switch
            id="solo_confirmados"
            checked={params.solo_confirmados}
            onCheckedChange={(checked) => updateField("solo_confirmados", checked)}
          />
        </div>
      </div>

      <div className="pt-4 border-t">
        <div className="flex items-center justify-between space-x-2 py-2">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_nota_pie">Incluir nota al pie</Label>
            <p className="text-xs text-muted-foreground">
              Agrega la nota explicativa sobre eventos respiratorios
            </p>
          </div>
          <Switch
            id="incluir_nota_pie"
            checked={params.incluir_nota_pie}
            onCheckedChange={(checked) => updateField("incluir_nota_pie", checked)}
          />
        </div>

        {params.incluir_nota_pie && (
          <Card className="p-3 mt-2 bg-muted/50">
            <p className="text-xs italic text-muted-foreground">
              *No se consideran los eventos respiratorios ya que forman parte del desarrollo
              de este boletín provincial.
            </p>
          </Card>
        )}
      </div>

      {/* Preview */}
      <div className="pt-4 border-t">
        <h4 className="font-medium text-sm mb-3">Vista Previa</h4>
        <Card className="p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Evento</th>
                <th className="text-right py-2">N° de casos</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="py-2">Sífilis*</td>
                <td className="text-right">48</td>
              </tr>
              <tr className="border-b">
                <td className="py-2">Intento de suicidio</td>
                <td className="text-right">10</td>
              </tr>
              <tr className="border-b">
                <td className="py-2">VIH</td>
                <td className="text-right">8</td>
              </tr>
              {params.top_n && params.top_n >= 5 && (
                <>
                  <tr className="border-b">
                    <td className="py-2">Chagas crónico</td>
                    <td className="text-right">3</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-2">APR</td>
                    <td className="text-right">3</td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
          <p className="text-xs text-muted-foreground mt-3">
            Datos de ejemplo. Los valores reales se generarán al crear el boletín.
          </p>
        </Card>
      </div>
    </div>
  );
}
