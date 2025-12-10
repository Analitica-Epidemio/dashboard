"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Database, FileText, Activity, Droplet } from "lucide-react";
import { cn } from "@/lib/utils";

interface TableConfig {
  queryType: string;
  title: string;
}

interface TableConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInsert: (config: TableConfig) => void;
}

const TABLE_TYPES = [
  {
    id: "top_enos",
    name: "Top ENOs",
    icon: Activity,
    description: "Eventos de notificación más frecuentes del período",
    color: "bg-green-50 border-green-200 hover:bg-green-100",
    columns: ["Evento", "Casos", "Tasa", "Variación"],
  },
  {
    id: "capacidad_hospitalaria",
    name: "Capacidad Hospitalaria",
    icon: Database,
    description: "Dotación de camas y ocupación por servicio",
    color: "bg-blue-50 border-blue-200 hover:bg-blue-100",
    columns: ["Servicio", "Total", "Ocupadas", "Disponibles"],
  },
  {
    id: "casos_suh",
    name: "Casos SUH",
    icon: FileText,
    description: "Descripción detallada de casos de Síndrome Urémico Hemolítico",
    color: "bg-red-50 border-red-200 hover:bg-red-100",
    columns: ["Fecha", "Edad", "Sexo", "Localidad", "Estado"],
  },
  {
    id: "virus_respiratorios_detalle",
    name: "Virus Respiratorios Detalle",
    icon: Activity,
    description: "Detección por agente etiológico y grupo etario",
    color: "bg-purple-50 border-purple-200 hover:bg-purple-100",
    columns: ["Virus", "< 2 años", "2-5 años", "5-18 años", "> 18 años"],
  },
  {
    id: "diarreas_agente",
    name: "Diarreas por Agente",
    icon: Droplet,
    description: "Casos de diarrea aguda según agente etiológico",
    color: "bg-orange-50 border-orange-200 hover:bg-orange-100",
    columns: ["Agente", "Casos", "Porcentaje", "Semana"],
  },
];

export function TableConfigDialog({ open, onOpenChange, onInsert }: TableConfigDialogProps) {
  const [step, setStep] = useState<"tableType" | "config">("tableType");
  const [config, setConfig] = useState<TableConfig>({
    queryType: "",
    title: "",
  });

  const handleInsert = () => {
    if (!config.queryType) return;
    onInsert(config);
    onOpenChange(false);
    // Reset
    setStep("tableType");
    setConfig({
      queryType: "",
      title: "",
    });
  };

  const handleBack = () => {
    setStep("tableType");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {step === "tableType" && "Selecciona el tipo de tabla"}
            {step === "config" && "Configuración de la tabla"}
          </DialogTitle>
        </DialogHeader>

        {/* Step 1: Table Type */}
        {step === "tableType" && (
          <div className="grid gap-2 py-4">
            {TABLE_TYPES.map((table) => (
              <button
                key={table.id}
                onClick={() => {
                  setConfig({ ...config, queryType: table.id });
                  setStep("config");
                }}
                className={cn(
                  "p-4 border-2 rounded-lg text-left transition-all",
                  table.color,
                  config.queryType === table.id && "ring-2 ring-blue-500"
                )}
              >
                <div className="flex items-start gap-3 mb-2">
                  <div className="p-2 bg-white rounded-md border">
                    <table.icon className="w-5 h-5 text-gray-700" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm mb-1">{table.name}</div>
                    <div className="text-xs text-gray-600">{table.description}</div>
                  </div>
                </div>
                <div className="pl-11">
                  <div className="flex gap-1 flex-wrap">
                    {table.columns.map((col, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-white rounded text-[10px] font-mono text-gray-600 border"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Step 2: Config */}
        {step === "config" && (
          <div className="space-y-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Título de la Tabla (opcional)</Label>
              <Input
                id="title"
                placeholder="Ej: Tabla N°1. Casos confirmados notificados en SNVS..."
                value={config.title}
                onChange={(e) => setConfig({ ...config, title: e.target.value })}
              />
              <p className="text-xs text-gray-500">
                Este título aparecerá como caption debajo de la tabla
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          {step === "config" && (
            <Button variant="outline" onClick={handleBack}>
              Atrás
            </Button>
          )}
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          {step === "config" && (
            <Button onClick={handleInsert}>Insertar Tabla</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
