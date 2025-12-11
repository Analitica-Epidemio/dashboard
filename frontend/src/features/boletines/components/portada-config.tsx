"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import type { PortadaConfig as PortadaConfigType } from "./types";

interface PortadaConfigProps {
  portada: PortadaConfigType;
  onChange: (portada: PortadaConfigType) => void;
}

export function PortadaConfig({ portada, onChange }: PortadaConfigProps) {
  const updateField = <K extends keyof PortadaConfigType>(
    field: K,
    value: PortadaConfigType[K]
  ) => {
    onChange({ ...portada, [field]: value });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-2xl">📄</span>
          <span>Configuración de Portada</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="titulo">Título Principal</Label>
          <Input
            id="titulo"
            value={portada.titulo}
            onChange={(e) => updateField("titulo", e.target.value)}
            placeholder="Ej: Boletín Epidemiológico Provincial"
          />
          <p className="text-xs text-muted-foreground">
            Este título aparecerá en la portada de todos los boletines generados con este
            template.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="subtitulo">Subtítulo (opcional)</Label>
          <Input
            id="subtitulo"
            value={portada.subtitulo || ""}
            onChange={(e) => updateField("subtitulo", e.target.value)}
            placeholder="Ej: Dirección Provincial de Epidemiología"
          />
        </div>

        <div className="flex items-center justify-between space-x-2 py-3 border-t">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_logo">Incluir logo provincial</Label>
            <p className="text-xs text-muted-foreground">
              Muestra el logo de la provincia en la portada
            </p>
          </div>
          <Switch
            id="incluir_logo"
            checked={portada.incluir_logo}
            onCheckedChange={(checked) => updateField("incluir_logo", checked)}
          />
        </div>

        {portada.incluir_logo && (
          <div className="space-y-2 ml-6 border-l-2 border-blue-200 pl-4">
            <Label htmlFor="logo_url" className="text-sm">
              URL del logo (opcional)
            </Label>
            <Input
              id="logo_url"
              value={portada.logo_url || ""}
              onChange={(e) => updateField("logo_url", e.target.value)}
              placeholder="/images/logo-provincia.png"
            />
            <p className="text-xs text-muted-foreground">
              Si está vacío, se usará el logo por defecto del sistema.
            </p>
          </div>
        )}

        <div className="flex items-center justify-between space-x-2 py-3 border-t">
          <div className="space-y-0.5">
            <Label htmlFor="incluir_texto_estandar">Incluir texto descriptivo estándar</Label>
            <p className="text-xs text-muted-foreground">
              Muestra el texto estándar sobre el SNVS 2.0 y la periodicidad del boletín
            </p>
          </div>
          <Switch
            id="incluir_texto_estandar"
            checked={portada.incluir_texto_estandar}
            onCheckedChange={(checked) =>
              updateField("incluir_texto_estandar", checked)
            }
          />
        </div>

        {portada.incluir_texto_estandar && (
          <div className="ml-6 border-l-2 border-blue-200 pl-4">
            <div className="text-xs text-muted-foreground bg-muted p-3 rounded-md space-y-2">
              <p className="font-medium">Preview del texto estándar:</p>
              <p className="italic">
                &quot;Este boletín es el resultado de la información proporcionada de manera
                sistemática por parte de los efectores de las cuatro Unidades de Gestión
                Descentralizadas (UGD) que conforman la provincia de Chubut...&quot;
              </p>
              <p className="text-[10px] opacity-70">
                Este texto se generará automáticamente con las fechas correspondientes a cada
                boletín.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
