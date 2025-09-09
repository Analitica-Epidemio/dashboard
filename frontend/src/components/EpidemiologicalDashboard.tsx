/**
 * Dashboard Principal de Epidemiología
 * Integra todos los charts epidemiológicos con filtros y navegación
 */

import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Calendar,
  BarChart3,
  TrendingUp,
  Users,
  MapPin,
  AlertTriangle,
  RefreshCw,
  Download,
  Settings,
  Filter
} from 'lucide-react';

// Importar todos los componentes de charts
import EndemicCorridorChart from './charts/EndemicCorridorChart';
import EpidemiologicalCurveChart from './charts/EpidemiologicalCurveChart';
import HistoricalTotalsChart from './charts/HistoricalTotalsChart';
import AgePyramidChart from './charts/AgePyramidChart';
import UGDPieChart from './charts/UGDPieChart';
import SuicideAttemptChart from './charts/SuicideAttemptChart';
import AnimalRabiesChart from './charts/AnimalRabiesChart';

// Hooks y tipos
import { 
  useEpidemiologicalFilters 
} from '../hooks/useEpidemiologicalData';
import {
  EpidemiologicalFilters,
  EndemicCorridorConfig,
} from '../types/epidemiological';

// Panel de filtros
interface FilterPanelProps {
  filters: EpidemiologicalFilters;
  onFiltersChange: (filters: Partial<EpidemiologicalFilters>) => void;
  onReset: () => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ 
  filters, 
  onFiltersChange, 
  onReset 
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros
          </h3>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              <Settings className="h-4 w-4 mr-1" />
              {showAdvanced ? 'Ocultar' : 'Avanzados'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Limpiar
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Filtros básicos */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Rango de fechas */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Período
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  value={filters.dateRange?.startDate || ''}
                  onChange={(e) => onFiltersChange({
                    dateRange: {
                      ...filters.dateRange,
                      startDate: e.target.value,
                      endDate: filters.dateRange?.endDate || '',
                    }
                  })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  type="date"
                  value={filters.dateRange?.endDate || ''}
                  onChange={(e) => onFiltersChange({
                    dateRange: {
                      startDate: filters.dateRange?.startDate || '',
                      endDate: e.target.value,
                    }
                  })}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* Áreas geográficas */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Áreas Geográficas
              </label>
              <select
                multiple
                value={filters.geographicAreas || []}
                onChange={(e) => onFiltersChange({
                  geographicAreas: Array.from(e.target.selectedOptions, option => option.value)
                })}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm w-full"
                size={3}
              >
                <option value="SUR_AP_COMODORO">Sur - Comodoro Rivadavia</option>
                <option value="NORTE_AP_NORTE">Norte - Área Norte</option>
                <option value="NORESTE_AP_TRELEW">Noreste - Trelew</option>
                <option value="NOROESTE_AP_ESQUEL">Noroeste - Esquel</option>
              </select>
            </div>

            {/* Tipos de eventos */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Tipos de Eventos
              </label>
              <select
                multiple
                value={filters.eventTypes || []}
                onChange={(e) => onFiltersChange({
                  eventTypes: Array.from(e.target.selectedOptions, option => option.value)
                })}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm w-full"
                size={3}
              >
                <option value="IRA">Infecciones Respiratorias Agudas</option>
                <option value="HANTAVIRUS">Hantavirus</option>
                <option value="RABIA_ANIMAL">Rabia Animal</option>
                <option value="INTENTO_SUICIDIO">Intento de Suicidio</option>
                <option value="MENINGITIS">Meningitis</option>
              </select>
            </div>
          </div>

          {/* Filtros avanzados */}
          {showAdvanced && (
            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Grupos de Edad
                  </label>
                  <select
                    multiple
                    value={filters.ageGroups || []}
                    onChange={(e) => onFiltersChange({
                      ageGroups: Array.from(e.target.selectedOptions, option => option.value)
                    })}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm w-full"
                    size={4}
                  >
                    <option value="0-4">0-4 años</option>
                    <option value="5-14">5-14 años</option>
                    <option value="15-24">15-24 años</option>
                    <option value="25-44">25-44 años</option>
                    <option value="45-64">45-64 años</option>
                    <option value="65+">65+ años</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Opciones
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.includeDeaths || false}
                        onChange={(e) => onFiltersChange({
                          includeDeaths: e.target.checked
                        })}
                        className="mr-2"
                      />
                      <span className="text-sm">Incluir datos de mortalidad</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tags de filtros activos */}
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            {filters.geographicAreas?.map(area => (
              <Badge key={area} variant="secondary">
                {area.replace(/_/g, ' ')}
              </Badge>
            ))}
            {filters.eventTypes?.map(type => (
              <Badge key={type} variant="secondary">
                {type.replace(/_/g, ' ')}
              </Badge>
            ))}
            {filters.includeDeaths && (
              <Badge variant="secondary">Con mortalidad</Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Configuraciones predeterminadas
const DEFAULT_ENDEMIC_CONFIG: EndemicCorridorConfig = {
  calculation: 'media',
  cumulative: false,
  logarithmic: false,
  movingWindow: 3,
  lastWeek: 52,
};

export const EpidemiologicalDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('corridor');
  const [endemicConfig, setEndemicConfig] = useState(DEFAULT_ENDEMIC_CONFIG);
  
  const {
    filters,
    updateFilters,
    resetFilters,
  } = useEpidemiologicalFilters({
    includeDeaths: true,
  });

  // Handlers para eventos de charts
  const handleWeekSelect = (week: number, year?: number) => {
    console.log(`Selected week ${week}`, year ? `of year ${year}` : '');
    // Implementar navegación o filtrado detallado
  };

  const handleLocationSelect = (location: string) => {
    console.log(`Selected location: ${location}`);
    // Implementar filtro por ubicación
  };

  const handleExportData = (chartType: string, format: 'csv' | 'excel') => {
    console.log(`Exporting ${chartType} as ${format}`);
    // Implementar exportación de datos
  };

  // Métricas de resumen
  const summaryMetrics = useMemo(() => {
    // Estas métricas vendrían del backend en un caso real
    return {
      totalCases: 15420,
      activeCases: 234,
      weeklyChange: 8.5,
      lastUpdated: new Date().toLocaleDateString(),
    };
  }, [filters]);

  return (
    <div className="space-y-6 p-6">
      {/* Header del Dashboard */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Dashboard Epidemiológico
          </h1>
          <p className="text-gray-600 mt-1">
            Sistema de vigilancia epidemiológica - Provincia del Chubut
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Métricas de resumen */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">
              {summaryMetrics.totalCases.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Casos Totales</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {summaryMetrics.activeCases.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Casos Activos</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-orange-600">
              +{summaryMetrics.weeklyChange}%
            </div>
            <div className="text-sm text-gray-600">Cambio Semanal</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-sm font-medium text-gray-700">
              Actualizado:
            </div>
            <div className="text-sm text-gray-600">
              {summaryMetrics.lastUpdated}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Panel de filtros */}
      <FilterPanel
        filters={filters}
        onFiltersChange={updateFilters}
        onReset={resetFilters}
      />

      {/* Tabs de charts */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="corridor" className="flex items-center gap-1">
            <TrendingUp className="h-4 w-4" />
            <span className="hidden sm:inline">Corredor</span>
          </TabsTrigger>
          <TabsTrigger value="curve" className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Curva</span>
          </TabsTrigger>
          <TabsTrigger value="historical" className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span className="hidden sm:inline">Históricos</span>
          </TabsTrigger>
          <TabsTrigger value="demographics" className="flex items-center gap-1">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Demografía</span>
          </TabsTrigger>
          <TabsTrigger value="ugd" className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            <span className="hidden sm:inline">UGD</span>
          </TabsTrigger>
          <TabsTrigger value="suicide" className="flex items-center gap-1">
            <AlertTriangle className="h-4 w-4" />
            <span className="hidden sm:inline">Suicidio</span>
          </TabsTrigger>
          <TabsTrigger value="rabies" className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">Rabia</span>
          </TabsTrigger>
        </TabsList>

        {/* Corredor Endémico */}
        <TabsContent value="corridor">
          <EndemicCorridorChart
            config={endemicConfig}
            filters={filters}
            onWeekSelect={handleWeekSelect}
            showCurrentWeekIndicator={true}
          />
        </TabsContent>

        {/* Curva Epidemiológica */}
        <TabsContent value="curve">
          <EpidemiologicalCurveChart
            filters={filters}
            onWeekSelect={handleWeekSelect}
            showMortalityData={filters.includeDeaths}
          />
        </TabsContent>

        {/* Totales Históricos */}
        <TabsContent value="historical">
          <HistoricalTotalsChart
            filters={filters}
            onYearSelect={(year) => console.log(`Selected year: ${year}`)}
            showMortalityData={filters.includeDeaths}
          />
        </TabsContent>

        {/* Demografia */}
        <TabsContent value="demographics">
          <AgePyramidChart
            filters={filters}
            onAgeGroupSelect={(ageGroup) => console.log(`Selected age group: ${ageGroup}`)}
          />
        </TabsContent>

        {/* UGD */}
        <TabsContent value="ugd">
          <UGDPieChart
            filters={filters}
            onUGDSelect={(ugdId) => console.log(`Selected UGD: ${ugdId}`)}
            showMortalityData={filters.includeDeaths}
          />
        </TabsContent>

        {/* Intento de Suicidio */}
        <TabsContent value="suicide">
          <SuicideAttemptChart
            filters={filters}
            onTimePointSelect={handleWeekSelect}
          />
        </TabsContent>

        {/* Rabia Animal */}
        <TabsContent value="rabies">
          <AnimalRabiesChart
            filters={filters}
            onLocationSelect={handleLocationSelect}
            onSpeciesSelect={(species) => console.log(`Selected species: ${species}`)}
          />
        </TabsContent>
      </Tabs>

      {/* Footer con información del sistema */}
      <div className="text-center text-sm text-gray-500 border-t pt-4">
        <p>
          Sistema de Vigilancia Epidemiológica - Ministerio de Salud del Chubut
        </p>
        <p>
          Datos actualizados hasta: {summaryMetrics.lastUpdated} | 
          Version 1.0.0
        </p>
      </div>
    </div>
  );
};

export default EpidemiologicalDashboard;