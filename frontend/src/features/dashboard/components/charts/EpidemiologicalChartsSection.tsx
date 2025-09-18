/**
 * Sección de Charts Epidemiológicos para integrar en DashboardContent
 * Permite seleccionar y mostrar diferentes tipos de análisis epidemiológicos
 */

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Calendar,
  MapPin,
  PieChart,
  TrendingUp,
  Users,
} from "lucide-react";
import { EndemicCorridorConfig, EpidemiologicalFilters } from "../../types";
import SuicideAttemptChart from "./SuicideAttemptChart";
import UGDPieChart from "./UGDPieChart";
import AgePyramidChart from "./AgePyramidChart";
import EndemicCorridorChart from "./EndemicCorridorChart";
import EpidemiologicalCurveChart from "./EpidemiologicalCurveChart";
import HistoricalTotalsChart from "./HistoricalTotalsChart";
import AnimalRabiesChart from "./AnimalRabiesChart";

interface EpidemiologicalChartsSectionProps {
  selectedGroup: { id: string; name: string } | null;
  selectedEvent: { id: string; name: string; description?: string | null | undefined } | null;
  filters: {
    selectedGroupId: string | null;
    selectedEventId: string | null;
  };
}

// Función para obtener la semana del año
const getWeekNumber = (date: Date): number => {
  const tempDate = new Date(date.getTime());
  tempDate.setHours(0, 0, 0, 0);
  tempDate.setDate(tempDate.getDate() + 3 - ((tempDate.getDay() + 6) % 7));
  const week1 = new Date(tempDate.getFullYear(), 0, 4);
  return (
    1 +
    Math.round(
      ((tempDate.getTime() - week1.getTime()) / 86400000 -
        3 +
        ((week1.getDay() + 6) % 7)) /
        7
    )
  );
};

// Configuración por defecto del corredor endémico
const DEFAULT_ENDEMIC_CONFIG: EndemicCorridorConfig = {
  calculation: "media",
  cumulative: false,
  logarithmic: false,
  movingWindow: 4,
  lastWeek: getWeekNumber(new Date()),
};

export const EpidemiologicalChartsSection: React.FC<
  EpidemiologicalChartsSectionProps
> = ({ selectedGroup, selectedEvent, filters }) => {
  const [activeChart, setActiveChart] = useState<string>(
    "epidemiological-curve"
  );

  // Convertir filtros del dashboard a filtros epidemiológicos
  const epidemiologicalFilters: EpidemiologicalFilters = useMemo(() => {
    return {
      selectedGroupId: filters.selectedGroupId,
      selectedEventId: filters.selectedEventId,
      // Agregar otros filtros según sea necesario
      dateRange: undefined,
      geographicAreas: undefined,
      ageGroups: undefined,
      eventTypes: undefined,
      includeDeaths: true,
    };
  }, [filters]);

  // Configuración de charts disponibles
  const chartOptions = [
    {
      id: "epidemiological-curve",
      name: "Curva Epidemiológica",
      description: "Análisis temporal de casos por semana epidemiológica",
      icon: TrendingUp,
      category: "temporal",
    },
    {
      id: "endemic-corridor",
      name: "Corredor Endémico",
      description: "Zonas epidémicas: éxito, seguridad y alerta",
      icon: Activity,
      category: "temporal",
    },
    {
      id: "historical-totals",
      name: "Totales Históricos",
      description: "Comparativa anual por área programática",
      icon: BarChart3,
      category: "temporal",
    },
    {
      id: "age-pyramid",
      name: "Pirámide Poblacional",
      description: "Distribución por edad y sexo",
      icon: Users,
      category: "demographic",
    },
    {
      id: "ugd-distribution",
      name: "Distribución UGD",
      description: "Casos por unidad de gestión de datos",
      icon: PieChart,
      category: "geographic",
    },
    {
      id: "suicide-attempt",
      name: "Intento de Suicidio",
      description: "Análisis especializado de casos de suicidio",
      icon: AlertTriangle,
      category: "specialized",
    },
    {
      id: "animal-rabies",
      name: "Rabia Animal",
      description: "Vigilancia epidemiológica de rabia en animales",
      icon: MapPin,
      category: "specialized",
    },
  ];

  const chartCategories = {
    temporal: "Análisis Temporal",
    demographic: "Análisis Demográfico",
    geographic: "Análisis Geográfico",
    specialized: "Análisis Especializado",
  };

  // Renderizar chart seleccionado
  const renderActiveChart = () => {
    const commonProps = {
      filters: epidemiologicalFilters,
      chartConfig: { height: 600 },
    };

    switch (activeChart) {
      case "epidemiological-curve":
        return (
          <EpidemiologicalCurveChart
            {...commonProps}
            showMortalityData={true}
            onWeekSelect={(week: number, year: number) => {
              console.log(`Semana seleccionada: ${week}, Año: ${year}`);
            }}
          />
        );

      case "endemic-corridor":
        return (
          <EndemicCorridorChart
            {...commonProps}
            config={DEFAULT_ENDEMIC_CONFIG}
            showCurrentWeekIndicator={true}
            onWeekSelect={(week: number) => {
              console.log(`Semana del corredor seleccionada: ${week}`);
            }}
          />
        );

      case "historical-totals":
        return (
          <HistoricalTotalsChart
            {...commonProps}
            chartType="line"
            showTrendIndicators={true}
            onYearSelect={(year: number) => {
              console.log(`Año seleccionado: ${year}`);
            }}
          />
        );

      case "age-pyramid":
        // Datos de ejemplo para la pirámide de edad
        const pyramidData = [
          { age: "0-4", sex: "M" as const, value: 150 },
          { age: "0-4", sex: "F" as const, value: 140 },
          { age: "5-9", sex: "M" as const, value: 130 },
          { age: "5-9", sex: "F" as const, value: 125 },
          { age: "10-14", sex: "M" as const, value: 120 },
          { age: "10-14", sex: "F" as const, value: 115 },
          { age: "15-19", sex: "M" as const, value: 110 },
          { age: "15-19", sex: "F" as const, value: 105 },
          { age: "20-24", sex: "M" as const, value: 95 },
          { age: "20-24", sex: "F" as const, value: 90 },
        ];
        return (
          <AgePyramidChart
            data={pyramidData}
            width={600}
            height={400}
          />
        );

      case "ugd-distribution":
        return (
          <UGDPieChart
            {...commonProps}
            chartType="pie"
            showMortalityData={true}
            onUGDSelect={(ugdName: string) => {
              console.log(`UGD seleccionada: ${ugdName}`);
            }}
          />
        );

      case "suicide-attempt":
        return (
          <SuicideAttemptChart
            {...commonProps}
            showDemographics={true}
            defaultView="temporal"
            onTimeRangeSelect={(
              startWeek: number,
              endWeek: number,
              year: number
            ) => {
              console.log(
                `Rango seleccionado: ${startWeek}-${endWeek}, Año: ${year}`
              );
            }}
          />
        );

      case "animal-rabies":
        return (
          <AnimalRabiesChart
            {...commonProps}
            defaultView="temporal"
            showPositivityRate={true}
            onSpeciesSelect={(species: string) => {
              console.log(`Especie seleccionada: ${species}`);
            }}
            onDateRangeSelect={(startDate: string, endDate: string) => {
              console.log(`Rango de fechas: ${startDate} - ${endDate}`);
            }}
          />
        );

      default:
        return (
          <div className="p-8 text-center text-gray-500">
            Chart no encontrado
          </div>
        );
    }
  };

  // Si no hay grupo seleccionado, mostrar mensaje
  if (!selectedGroup) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>
              Selecciona un grupo para acceder a los análisis epidemiológicos
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con información del contexto */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Análisis Epidemiológicos
          </CardTitle>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">Grupo: {selectedGroup.name}</Badge>
            {selectedEvent && (
              <Badge variant="outline">Evento: {selectedEvent.name}</Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Selector de charts por categorías */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Seleccionar Tipo de Análisis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="w-full">
            <div className="space-y-4">
              {Object.entries(chartCategories).map(
                ([categoryId, categoryName]) => {
                  const categoryCharts = chartOptions.filter(
                    (chart) => chart.category === categoryId
                  );

                  if (categoryCharts.length === 0) return null;

                  return (
                    <div key={categoryId} className="space-y-2">
                      <h4 className="text-sm font-semibold text-gray-700">
                        {categoryName}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {categoryCharts.map((chart) => {
                          const Icon = chart.icon;
                          return (
                            <Button
                              key={chart.id}
                              variant={
                                activeChart === chart.id ? "default" : "outline"
                              }
                              className="h-auto p-4 flex flex-col items-start text-left"
                              onClick={() => setActiveChart(chart.id)}
                            >
                              <div className="flex items-center gap-2 mb-2">
                                <Icon className="h-4 w-4" />
                                <span className="font-medium">
                                  {chart.name}
                                </span>
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {chart.description}
                              </span>
                            </Button>
                          );
                        })}
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart activo */}
      <div>{renderActiveChart()}</div>
    </div>
  );
};
