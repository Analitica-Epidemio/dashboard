"use client";

import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LineChart, BarChart3, PieChart, TrendingUp, Activity, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChartsDisponibles } from "@/features/boletines/api";
import { GrupoEventoSelector } from "../grupo-evento-selector";
import { PeriodSelector } from "./period-selector";

interface ChartConfig {
  chartId: number;
  chartCode: string;
  title: string;
  selectedGroups: Set<string>;
  selectedEvents: Set<string>;
  fechaDesde: Date | null;
  fechaHasta: Date | null;
}

interface ChartConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInsert: (config: ChartConfig) => void;
  initialConfig?: Partial<ChartConfig> & { chartId: number; chartCode: string };
}

const CHART_TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  line: LineChart,
  bar: BarChart3,
  pie: PieChart,
  area: Activity,
  corridor: TrendingUp,
  map: Activity,
  metric: Activity,
  heatmap: Activity,
};

export function ChartConfigDialog({ open, onOpenChange, onInsert, initialConfig }: ChartConfigDialogProps) {
  const { data: chartsData, isLoading } = useChartsDisponibles();
  const [step, setStep] = useState<"chart" | "config">("chart");
  const [config, setConfig] = useState<ChartConfig>({
    chartId: 0,
    chartCode: "",
    title: "",
    selectedGroups: new Set<string>(),
    selectedEvents: new Set<string>(),
    fechaDesde: null,
    fechaHasta: null,
  });

  // Cargar valores iniciales si estamos editando
  React.useEffect(() => {
    if (open && initialConfig) {
      setConfig({
        chartId: initialConfig.chartId,
        chartCode: initialConfig.chartCode,
        title: initialConfig.title || "",
        selectedGroups: initialConfig.selectedGroups || new Set<string>(),
        selectedEvents: initialConfig.selectedEvents || new Set<string>(),
        fechaDesde: initialConfig.fechaDesde || null,
        fechaHasta: initialConfig.fechaHasta || null,
      });
      // Si tenemos initialConfig, ir directo al paso de config
      setStep("config");
    } else if (open && !initialConfig) {
      // Reset cuando abrimos para insertar nuevo
      setConfig({
        chartId: 0,
        chartCode: "",
        title: "",
        selectedGroups: new Set<string>(),
        selectedEvents: new Set<string>(),
        fechaDesde: null,
        fechaHasta: null,
      });
      setStep("chart");
    }
  }, [open, initialConfig]);

  const charts = chartsData?.data?.charts || [];

  const handleInsert = () => {
    if (!config.chartId) return;
    if (!config.fechaDesde || !config.fechaHasta) return; // Fechas requeridas
    onInsert(config);
    onOpenChange(false);
    // Reset
    setStep("chart");
    setConfig({
      chartId: 0,
      chartCode: "",
      title: "",
      selectedGroups: new Set<string>(),
      selectedEvents: new Set<string>(),
      fechaDesde: null,
      fechaHasta: null,
    });
  };

  const handleBack = () => {
    setStep("chart");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] sm:max-w-[900px] lg:max-w-[1100px] max-h-[90vh] flex flex-col p-0 gap-0">
        <DialogHeader className="px-6 pt-6 pb-4 shrink-0">
          <DialogTitle>
            {step === "chart" && "Selecciona el gráfico"}
            {step === "config" && "Configuración del gráfico"}
          </DialogTitle>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 px-6">

        {/* Step 1: Select Chart */}
        {step === "chart" && (
          <>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Cargando gráficos...</span>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 py-4">
                {charts.map((chart) => {
                  const Icon = CHART_TYPE_ICONS[chart.tipo_visualizacion] || Activity;
                  return (
                    <button
                      key={chart.id}
                      onClick={() => {
                        setConfig({
                          ...config,
                          chartId: chart.id,
                          chartCode: chart.codigo,
                        });
                        setStep("config");
                      }}
                      className={cn(
                        "p-4 border-2 rounded-lg text-left transition-all hover:shadow-md",
                        config.chartId === chart.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300"
                      )}
                    >
                      <div className="flex items-start gap-3 mb-2">
                        <div className="p-2 bg-white rounded-md border">
                          <Icon className="w-5 h-5 text-gray-700" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-sm mb-1">{chart.nombre}</div>
                          {chart.descripcion && (
                            <div className="text-xs text-gray-500 line-clamp-2">
                              {chart.descripcion}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="pl-11">
                        <span className="text-[10px] px-2 py-0.5 bg-gray-100 rounded font-mono text-gray-600">
                          {chart.tipo_visualizacion}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* Step 2: Config */}
        {step === "config" && (
          <div className="space-y-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Título del Gráfico (opcional)</Label>
              <Input
                id="title"
                placeholder="Ej: Gráfico N°1. Casos por semana epidemiológica..."
                value={config.title}
                onChange={(e) => setConfig({ ...config, title: e.target.value })}
              />
            </div>

            <div className="grid gap-2">
              <Label>Período de Análisis *</Label>
              <PeriodSelector
                fechaDesde={config.fechaDesde}
                fechaHasta={config.fechaHasta}
                onPeriodChange={(desde, hasta) =>
                  setConfig({ ...config, fechaDesde: desde, fechaHasta: hasta })
                }
              />
              {(!config.fechaDesde || !config.fechaHasta) && (
                <p className="text-xs text-red-500">
                  El período es requerido para renderizar el gráfico
                </p>
              )}
            </div>

            <div className="grid gap-2">
              <Label>Seleccionar Grupos y Eventos</Label>
              <GrupoEventoSelector
                selectedGroups={config.selectedGroups}
                selectedEvents={config.selectedEvents}
                onSelectionChange={(grupos, eventos) =>
                  setConfig({ ...config, selectedGroups: grupos, selectedEvents: eventos })
                }
              />
            </div>
          </div>
        )}
        </div>

        <DialogFooter className="px-6 pb-6 pt-4 shrink-0">
          {step === "config" && (
            <Button variant="outline" onClick={handleBack}>
              Atrás
            </Button>
          )}
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          {step === "config" && (
            <Button
              onClick={handleInsert}
              disabled={!config.fechaDesde || !config.fechaHasta}
            >
              Insertar Gráfico
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
