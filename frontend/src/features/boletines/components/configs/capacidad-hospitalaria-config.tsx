"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import type { CapacidadHospitalariaParams } from "../types";

interface CapacidadHospitalariaConfigProps {
  params: CapacidadHospitalariaParams;
  onChange: (params: CapacidadHospitalariaParams) => void;
}

const HOSPITALES_DISPONIBLES = [
  { codigo: "HZPM", nombre: "Hospital Zonal Andrés Isola (Puerto Madryn)" },
  { codigo: "HZTW", nombre: "Hospital Zonal de Trelew" },
  { codigo: "HRCR", nombre: "Hospital Regional Comodoro Rivadavia" },
  { codigo: "HSRW", nombre: "Hospital Sub Zonal Rawson - Santa Teresita" },
];

export function CapacidadHospitalariaConfig({
  params,
  onChange,
}: CapacidadHospitalariaConfigProps) {
  const updateField = <K extends keyof CapacidadHospitalariaParams>(
    field: K,
    value: CapacidadHospitalariaParams[K]
  ) => {
    onChange({ ...params, [field]: value });
  };

  const toggleHospital = (codigo: string) => {
    const currentHospitales = params.hospitales || [];
    const hospitales = currentHospitales.includes(codigo)
      ? currentHospitales.filter((h) => h !== codigo)
      : [...currentHospitales, codigo];
    updateField("hospitales", hospitales);
  };

  return (
    <div className="space-y-6">
      <div>
        <Label htmlFor="ultimas_n_semanas">Período de análisis</Label>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-sm text-muted-foreground">Últimas</span>
          <Input
            id="ultimas_n_semanas"
            type="number"
            min={1}
            max={26}
            value={params.ultimas_n_semanas}
            onChange={(e) =>
              updateField("ultimas_n_semanas", parseInt(e.target.value) || 6)
            }
            className="w-20 text-center"
          />
          <span className="text-sm text-muted-foreground">semanas</span>
        </div>
      </div>

      <div className="space-y-3 pt-4 border-t">
        <Label>Hospitales a incluir</Label>
        {HOSPITALES_DISPONIBLES.map((hospital) => (
          <div
            key={hospital.codigo}
            className="flex items-center space-x-2 py-2 border-b last:border-0"
          >
            <Checkbox
              id={hospital.codigo}
              checked={params.hospitales?.includes(hospital.codigo) || false}
              onCheckedChange={() => toggleHospital(hospital.codigo)}
            />
            <label
              htmlFor={hospital.codigo}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex-1"
            >
              <div className="font-semibold">{hospital.codigo}</div>
              <div className="text-xs text-muted-foreground">{hospital.nombre}</div>
            </label>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between space-x-2 pt-4 border-t">
        <div className="space-y-0.5">
          <Label htmlFor="mostrar_dotacion">Mostrar tabla de dotación de camas</Label>
          <p className="text-xs text-muted-foreground">
            Tabla con dotación total de camas por tipo y hospital
          </p>
        </div>
        <Switch
          id="mostrar_dotacion"
          checked={params.mostrar_dotacion}
          onCheckedChange={(checked) => updateField("mostrar_dotacion", checked)}
        />
      </div>
    </div>
  );
}
