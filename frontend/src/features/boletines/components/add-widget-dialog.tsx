"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Widget, WidgetType } from "./widgets/types";

interface AddWidgetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddWidget: (widget: Widget) => void;
}

export function AddWidgetDialog({ open, onOpenChange, onAddWidget }: AddWidgetDialogProps) {
  const [step, setStep] = useState(1);
  const [widgetType, setWidgetType] = useState<WidgetType | null>(null);
  const [title, setTitle] = useState("");
  const [dataSource, setDataSource] = useState<"manual" | "query">("query");
  const [queryEndpoint, setQueryEndpoint] = useState("");

  const handleReset = () => {
    setStep(1);
    setWidgetType(null);
    setTitle("");
    setDataSource("query");
    setQueryEndpoint("");
  };

  const handleClose = () => {
    handleReset();
    onOpenChange(false);
  };

  const handleNext = () => {
    if (step === 1 && widgetType) {
      setStep(2);
    } else if (step === 2) {
      setStep(3);
    }
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleAdd = () => {
    if (!widgetType) return;

    const baseWidget = {
      id: `widget-${Date.now()}`,
      position: { x: 0, y: 0, w: 4, h: 3 },
      title: title || `Nuevo ${widgetType}`,
      visual_config: {
        show_title: true,
        show_description: false,
        config: {},
      },
    };

    let newWidget: Widget;

    if (widgetType === "kpi") {
      newWidget = {
        ...baseWidget,
        type: "kpi" as const,
        data_config: {
          source: dataSource,
          ...(dataSource === "query" && queryEndpoint
            ? { query_id: queryEndpoint, query_params: {} }
            : {
                manual_data: {
                  value: 0,
                  label: null,
                  comparison: null,
                },
              }),
        },
      };
    } else {
      newWidget = {
        ...baseWidget,
        type: widgetType,
        data_config: {
          source: dataSource,
          ...(dataSource === "query" && queryEndpoint
            ? { query_id: queryEndpoint, query_params: {} }
            : { manual_data: {} }),
        },
      };
    }

    onAddWidget(newWidget);
    handleClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Agregar Widget</DialogTitle>
          <DialogDescription>
            Paso {step} de 3: {step === 1 ? "Tipo de Widget" : step === 2 ? "Configuración" : "Fuente de Datos"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {step === 1 && (
            <div className="space-y-4">
              <Label>Selecciona el tipo de widget</Label>
              <div className="grid grid-cols-3 gap-3">
                <WidgetTypeCard
                  type="kpi"
                  label="KPI"
                  description="Métrica clave"
                  selected={widgetType === "kpi"}
                  onClick={() => setWidgetType("kpi")}
                />
                <WidgetTypeCard
                  type="table"
                  label="Tabla"
                  description="Datos tabulares"
                  selected={widgetType === "table"}
                  onClick={() => setWidgetType("table")}
                />
                <WidgetTypeCard
                  type="line"
                  label="Líneas"
                  description="Series temporales"
                  selected={widgetType === "line"}
                  onClick={() => setWidgetType("line")}
                />
                <WidgetTypeCard
                  type="bar"
                  label="Barras"
                  description="Comparación"
                  selected={widgetType === "bar"}
                  onClick={() => setWidgetType("bar")}
                />
                <WidgetTypeCard
                  type="pie"
                  label="Circular"
                  description="Distribución"
                  selected={widgetType === "pie"}
                  onClick={() => setWidgetType("pie")}
                />
                <WidgetTypeCard
                  type="map"
                  label="Mapa"
                  description="Geográfico"
                  selected={widgetType === "map"}
                  onClick={() => setWidgetType("map")}
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Título del Widget</Label>
                <Input
                  id="title"
                  placeholder="Ej: Total de Casos, Top ENOs, etc."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <Tabs value={dataSource} onValueChange={(v) => setDataSource(v as "manual" | "query")}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="query">Desde Endpoint</TabsTrigger>
                  <TabsTrigger value="manual">Datos Manuales</TabsTrigger>
                </TabsList>

                <TabsContent value="query" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="endpoint">Endpoint</Label>
                    <Select value={queryEndpoint} onValueChange={setQueryEndpoint}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona un endpoint" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="/analytics/kpis">Analytics - KPIs</SelectItem>
                        <SelectItem value="/analytics/top-enos">Analytics - Top ENOs</SelectItem>
                        <SelectItem value="/analytics/tendencias">Analytics - Tendencias</SelectItem>
                        <SelectItem value="/charts/time-series">Charts - Series Temporales</SelectItem>
                        <SelectItem value="/eventos">Eventos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Los datos se cargarán automáticamente desde el endpoint seleccionado
                  </p>
                </TabsContent>

                <TabsContent value="manual" className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Configurarás los datos manualmente después de crear el widget
                  </p>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>

        <DialogFooter>
          <div className="flex items-center justify-between w-full">
            <div>
              {step > 1 && (
                <Button variant="ghost" onClick={handleBack}>
                  Atrás
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleClose}>
                Cancelar
              </Button>
              {step < 3 ? (
                <Button onClick={handleNext} disabled={step === 1 && !widgetType}>
                  Siguiente
                </Button>
              ) : (
                <Button onClick={handleAdd} disabled={!widgetType}>
                  Agregar Widget
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface WidgetTypeCardProps {
  type: WidgetType;
  label: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}

function WidgetTypeCard({ label, description, selected, onClick }: WidgetTypeCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        relative flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all
        ${selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent"}
      `}
    >
      <div className="font-medium">{label}</div>
      <div className="text-xs text-muted-foreground mt-1">{description}</div>
    </button>
  );
}
