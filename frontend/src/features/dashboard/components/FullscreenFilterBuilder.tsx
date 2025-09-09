/**
 * Fullscreen Filter Builder Component
 * Full-screen interface for building filter combinations
 */

import React, { useState } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DateRangePicker } from '@/components/DateRangePicker';
import { 
  Plus,
  Filter,
  X,
  Play,
  CalendarDays,
  Layers,
  Trash2,
  Copy,
  Check,
} from 'lucide-react';
import { GroupSelector } from './GroupSelector';
import { EventSelector } from './EventSelector';

interface FilterCombination {
  id: string;
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  label?: string;
  color?: string;
}

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface FullscreenFilterBuilderProps {
  groups: any[];
  availableEvents: any[];
  onApplyFilters: (dateRange: DateRange, combinations: FilterCombination[]) => void;
  groupsLoading: boolean;
  eventsLoading: boolean;
  groupsError: Error | null;
  eventsError: Error | null;
}

// Predefined colors for combinations
const COMBINATION_COLORS = [
  'bg-blue-100 border-blue-300',
  'bg-green-100 border-green-300',
  'bg-purple-100 border-purple-300',
  'bg-yellow-100 border-yellow-300',
  'bg-pink-100 border-pink-300',
  'bg-indigo-100 border-indigo-300',
];

export const FullscreenFilterBuilder: React.FC<FullscreenFilterBuilderProps> = ({
  groups,
  availableEvents,
  onApplyFilters,
  groupsLoading,
  eventsLoading,
  groupsError,
  eventsError,
}) => {
  // Estado para el rango de fechas global
  const [dateRange, setDateRange] = useState<DateRange>({
    from: new Date(new Date().setMonth(new Date().getMonth() - 3)), // Últimos 3 meses
    to: new Date(),
  });

  // Estado para las combinaciones de filtros
  const [filterCombinations, setFilterCombinations] = useState<FilterCombination[]>([]);
  
  // Estado para el filtro que se está construyendo
  const [currentFilter, setCurrentFilter] = useState<FilterCombination>({
    id: '',
    groupId: null,
    eventIds: [],
  });

  // Estado para controlar qué eventos están disponibles para el grupo seleccionado
  const [currentAvailableEvents, setCurrentAvailableEvents] = useState<any[]>([]);

  // Agregar una nueva combinación de filtros
  const addFilterCombination = () => {
    if (!currentFilter.groupId) return;

    const group = groups.find(g => String(g.id) === currentFilter.groupId);
    const selectedEvents = currentAvailableEvents.filter(e => 
      currentFilter.eventIds.includes(e.id)
    );

    const newCombination: FilterCombination = {
      id: `filter-${Date.now()}`,
      groupId: currentFilter.groupId,
      groupName: group?.name,
      eventIds: currentFilter.eventIds.length > 0 ? currentFilter.eventIds : 
                currentAvailableEvents.map(e => e.id),
      eventNames: currentFilter.eventIds.length > 0 ? 
                  selectedEvents.map(e => e.name) : 
                  ['Todos los eventos'],
      color: COMBINATION_COLORS[filterCombinations.length % COMBINATION_COLORS.length],
    };

    setFilterCombinations([...filterCombinations, newCombination]);
    
    // Limpiar el filtro actual
    setCurrentFilter({
      id: '',
      groupId: null,
      eventIds: [],
    });
    setCurrentAvailableEvents([]);
  };

  // Eliminar una combinación de filtros
  const removeFilterCombination = (id: string) => {
    setFilterCombinations(filterCombinations.filter(f => f.id !== id));
  };

  // Duplicar una combinación de filtros
  const duplicateFilterCombination = (combination: FilterCombination) => {
    const newCombination = {
      ...combination,
      id: `filter-${Date.now()}`,
      label: `${combination.label || combination.groupName} (copia)`,
      color: COMBINATION_COLORS[filterCombinations.length % COMBINATION_COLORS.length],
    };
    setFilterCombinations([...filterCombinations, newCombination]);
  };

  // Manejar cambio de grupo
  const handleGroupChange = (groupId: string | null) => {
    setCurrentFilter({
      ...currentFilter,
      groupId: groupId,
      eventIds: [],
    });
    
    if (groupId) {
      // Filtrar eventos por groupId (ambos son strings)
      const groupEvents = availableEvents.filter(e => e.groupId === groupId);
      setCurrentAvailableEvents(groupEvents);
    } else {
      setCurrentAvailableEvents([]);
    }
  };

  // Manejar selección de eventos
  const handleEventToggle = (eventId: number) => {
    setCurrentFilter(prev => ({
      ...prev,
      eventIds: prev.eventIds.includes(eventId)
        ? prev.eventIds.filter(id => id !== eventId)
        : [...prev.eventIds, eventId],
    }));
  };

  // Select/Deselect all events
  const toggleAllEvents = () => {
    if (currentFilter.eventIds.length === currentAvailableEvents.length) {
      setCurrentFilter(prev => ({ ...prev, eventIds: [] }));
    } else {
      setCurrentFilter(prev => ({ 
        ...prev, 
        eventIds: currentAvailableEvents.map(e => e.id) 
      }));
    }
  };

  // Aplicar filtros
  const handleApplyFilters = () => {
    onApplyFilters(dateRange, filterCombinations);
  };

  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return 'Seleccionar rango';
    return `${format(dateRange.from, 'd MMM yyyy', { locale: es })} - ${format(dateRange.to, 'd MMM yyyy', { locale: es })}`;
  };

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Configurar Análisis Comparativo
          </h1>
          <p className="text-gray-600">
            Define el período de tiempo y las combinaciones de filtros para tu análisis
          </p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Date Range & Filter Builder */}
          <div className="lg:col-span-2 space-y-6">
            {/* Date Range Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarDays className="h-5 w-5" />
                  Período de Análisis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Enhanced Date Range Picker */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Selecciona el período de análisis
                    </label>
                    <DateRangePicker
                      value={dateRange}
                      onChange={setDateRange}
                      className="w-full"
                    />
                  </div>

                  {/* Date range summary */}
                  {dateRange.from && dateRange.to && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-700 mb-1">Período seleccionado</p>
                          <p className="text-lg font-semibold text-blue-900">
                            {formatDateRange()}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-blue-700 mb-1">Duración</p>
                          <p className="text-lg font-semibold text-blue-900">
                            {Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60 * 24)) + 1} días
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Filter Builder Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-5 w-5" />
                  Constructor de Combinaciones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Group selector */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      1. Selecciona un Grupo de Eventos
                    </label>
                    <GroupSelector
                      groups={groups}
                      selectedGroupId={currentFilter.groupId}
                      onGroupChange={handleGroupChange}
                      loading={groupsLoading}
                      error={groupsError}
                    />
                  </div>

                  {/* Event selector */}
                  {currentFilter.groupId && currentAvailableEvents.length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-700">
                          2. Selecciona Eventos Específicos (opcional)
                        </label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={toggleAllEvents}
                        >
                          {currentFilter.eventIds.length === currentAvailableEvents.length ? (
                            <>
                              <X className="h-3 w-3 mr-1" />
                              Deseleccionar todos
                            </>
                          ) : (
                            <>
                              <Check className="h-3 w-3 mr-1" />
                              Seleccionar todos
                            </>
                          )}
                        </Button>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto bg-white">
                        <div className="grid grid-cols-2 gap-2">
                          {currentAvailableEvents.map((event) => (
                            <label
                              key={event.id}
                              className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                            >
                              <input
                                type="checkbox"
                                checked={currentFilter.eventIds.includes(event.id)}
                                onChange={() => handleEventToggle(event.id)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className="text-sm text-gray-700">{event.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Si no seleccionas ninguno, se incluirán todos los eventos del grupo
                      </p>
                    </div>
                  )}

                  {/* Add button */}
                  {currentFilter.groupId && (
                    <div className="flex justify-end">
                      <Button
                        onClick={addFilterCombination}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Plus className="h-4 w-4 mr-2" />
                        Agregar Combinación
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Added Combinations */}
          <div className="space-y-6">
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="h-5 w-5" />
                    Combinaciones ({filterCombinations.length})
                  </CardTitle>
                  {filterCombinations.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setFilterCombinations([])}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      Limpiar
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {filterCombinations.length === 0 ? (
                  <div className="text-center py-12">
                    <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">
                      No hay combinaciones agregadas
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Agrega al menos una para continuar
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filterCombinations.map((combination, index) => (
                      <div 
                        key={combination.id} 
                        className="border rounded-lg p-3 bg-white hover:shadow-sm transition-shadow"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 flex-1">
                            <Badge variant="outline" className="text-xs font-semibold">
                              {index + 1}
                            </Badge>
                            <div className="flex-1">
                              <span className="text-sm font-medium text-gray-900">
                                {combination.groupName}
                              </span>
                              <span className="text-xs text-gray-500 ml-2">
                                {combination.eventIds.length === 0 ? (
                                  'Todos los eventos'
                                ) : combination.eventIds.length === 1 ? (
                                  `1 evento`
                                ) : (
                                  `${combination.eventIds.length} eventos`
                                )}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6"
                              onClick={() => duplicateFilterCombination(combination)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6 hover:text-red-600"
                              onClick={() => removeFilterCombination(combination.id)}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                        {combination.eventNames && combination.eventNames.length > 0 && combination.eventNames[0] !== 'Todos los eventos' && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {combination.eventNames.slice(0, 3).map((name, i) => (
                              <span key={i} className="text-xs text-gray-600">
                                {name}{i < Math.min(2, combination.eventNames.length - 1) && ','}
                              </span>
                            ))}
                            {combination.eventNames.length > 3 && (
                              <span className="text-xs text-gray-500">
                                +{combination.eventNames.length - 3} más
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Apply button */}
                {filterCombinations.length > 0 && (
                  <div className="mt-6">
                    <Button 
                      className="w-full bg-green-600 hover:bg-green-700" 
                      size="lg"
                      onClick={handleApplyFilters}
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Aplicar y Analizar ({filterCombinations.length} {filterCombinations.length === 1 ? 'combinación' : 'combinaciones'})
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};