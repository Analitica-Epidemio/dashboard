/**
 * Filter Builder Component
 * Allows creating multiple filter combinations for comparative analysis
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Calendar,
  Plus,
  Filter,
  X,
  Play,
  CalendarDays,
  Layers,
  Trash2,
  Copy,
} from 'lucide-react';
import { GroupSelector } from './GroupSelector';
import { EventSelector } from './EventSelector';

interface FilterCombination {
  id: string;
  groupId: number | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  label?: string;
}

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface FilterBuilderProps {
  groups: any[];
  availableEvents: any[];
  onApplyFilters: (dateRange: DateRange, combinations: FilterCombination[]) => void;
  groupsLoading: boolean;
  eventsLoading: boolean;
  groupsError: Error | null;
  eventsError: Error | null;
}

export const FilterBuilder: React.FC<FilterBuilderProps> = ({
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

    const group = groups.find(g => g.id === currentFilter.groupId);
    const selectedEvents = currentAvailableEvents.filter(e => 
      currentFilter.eventIds.includes(e.id)
    );

    const newCombination: FilterCombination = {
      id: `filter-${Date.now()}`,
      groupId: currentFilter.groupId,
      groupName: group?.name,
      eventIds: currentFilter.eventIds.length > 0 ? currentFilter.eventIds : 
                currentAvailableEvents.map(e => e.id), // Si no hay eventos seleccionados, usar todos
      eventNames: currentFilter.eventIds.length > 0 ? 
                  selectedEvents.map(e => e.name) : 
                  ['Todos los eventos'],
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
    };
    setFilterCombinations([...filterCombinations, newCombination]);
  };

  // Manejar cambio de grupo
  const handleGroupChange = (group: any) => {
    setCurrentFilter({
      ...currentFilter,
      groupId: group?.id || null,
      eventIds: [],
    });
    
    // Filtrar eventos disponibles para este grupo
    if (group) {
      const groupEvents = availableEvents.filter(e => e.grupo_evento_id === group.id);
      setCurrentAvailableEvents(groupEvents);
    } else {
      setCurrentAvailableEvents([]);
    }
  };

  // Manejar selección de eventos (múltiple)
  const handleEventToggle = (eventId: number) => {
    setCurrentFilter(prev => ({
      ...prev,
      eventIds: prev.eventIds.includes(eventId)
        ? prev.eventIds.filter(id => id !== eventId)
        : [...prev.eventIds, eventId],
    }));
  };

  // Aplicar filtros
  const handleApplyFilters = () => {
    if (filterCombinations.length === 0 && currentFilter.groupId) {
      // Si hay un filtro en construcción pero no se agregó, agregarlo automáticamente
      addFilterCombination();
      setTimeout(() => {
        onApplyFilters(dateRange, [...filterCombinations, {
          id: `filter-${Date.now()}`,
          groupId: currentFilter.groupId,
          groupName: groups.find(g => g.id === currentFilter.groupId)?.name,
          eventIds: currentFilter.eventIds.length > 0 ? currentFilter.eventIds : 
                    currentAvailableEvents.map(e => e.id),
          eventNames: currentFilter.eventIds.length > 0 ? 
                      currentAvailableEvents.filter(e => currentFilter.eventIds.includes(e.id)).map(e => e.name) : 
                      ['Todos los eventos'],
        }]);
      }, 100);
    } else {
      onApplyFilters(dateRange, filterCombinations);
    }
  };

  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return 'Seleccionar rango';
    const options: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short', year: 'numeric' };
    return `${dateRange.from.toLocaleDateString('es', options)} - ${dateRange.to.toLocaleDateString('es', options)}`;
  };

  return (
    <div className="w-96 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Constructor de Filtros
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Define múltiples combinaciones para comparar
            </p>
          </div>

          <Separator />

          {/* Rango de Fechas Global */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <CalendarDays className="h-4 w-4" />
              Rango de Fechas Global
            </label>
            <Button 
              variant="outline" 
              className="w-full justify-start text-left font-normal"
              onClick={() => {/* TODO: Abrir date picker */}}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {formatDateRange()}
            </Button>
            <p className="text-xs text-gray-500 mt-1">
              Aplicado a todas las combinaciones
            </p>
          </div>

          <Separator />

          {/* Constructor de Filtros */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Layers className="h-4 w-4" />
                Agregar Combinación
              </label>
              {currentFilter.groupId && (
                <Button
                  size="sm"
                  variant="default"
                  onClick={addFilterCombination}
                  className="h-8"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Agregar
                </Button>
              )}
            </div>

            {/* Selector de Grupo */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">
                Grupo de Eventos
              </label>
              <GroupSelector
                groups={groups}
                selectedGroupId={currentFilter.groupId}
                onGroupChange={handleGroupChange}
                loading={groupsLoading}
                error={groupsError?.message || null}
              />
            </div>

            {/* Selector de Eventos (Multi-select) */}
            {currentFilter.groupId && currentAvailableEvents.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  Eventos Específicos (opcional)
                </label>
                <div className="border border-gray-200 rounded-lg p-2 max-h-32 overflow-y-auto">
                  <div className="space-y-1">
                    {currentAvailableEvents.map((event) => (
                      <label
                        key={event.id}
                        className="flex items-center gap-2 p-1.5 hover:bg-gray-50 rounded cursor-pointer"
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
                  Sin selección = Todos los eventos del grupo
                </p>
              </div>
            )}

            {/* Selector de Clasificaciones */}
            {currentFilter.groupId && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  Clasificaciones (opcional)
                </label>
                <ClassificationSelector
                  selectedClassifications={currentFilter.clasificaciones || []}
                  onClassificationChange={(classifications) =>
                    setCurrentFilter({
                      ...currentFilter,
                      clasificaciones: classifications,
                    })
                  }
                  placeholder="Todas las clasificaciones"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Filtrar por estado epidemiológico
                </p>
              </div>
            )}
          </div>

          <Separator />

          {/* Combinaciones Agregadas */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Combinaciones ({filterCombinations.length})
              </label>
              {filterCombinations.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setFilterCombinations([])}
                  className="h-8 text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  Limpiar
                </Button>
              )}
            </div>

            {filterCombinations.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500 text-center">
                    No hay combinaciones agregadas
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {filterCombinations.map((combination, index) => (
                  <Card key={combination.id} className="bg-gray-50">
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs">
                              #{index + 1}
                            </Badge>
                            <span className="text-sm font-medium text-gray-900">
                              {combination.groupName}
                            </span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex flex-wrap gap-1">
                              {combination.eventNames?.slice(0, 3).map((name, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {name}
                                </Badge>
                              ))}
                              {combination.eventNames && combination.eventNames.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{combination.eventNames.length - 3}
                                </Badge>
                              )}
                            </div>
                            {combination.clasificaciones && combination.clasificaciones.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                <ClassificationBadges
                                  classifications={combination.clasificaciones}
                                />
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 ml-2">
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
                            className="h-6 w-6 text-red-600"
                            onClick={() => removeFilterCombination(combination.id)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer con botón de aplicar */}
      <div className="border-t border-gray-200 p-4">
        <Button 
          className="w-full" 
          size="lg"
          onClick={handleApplyFilters}
          disabled={filterCombinations.length === 0 && !currentFilter.groupId}
        >
          <Play className="h-4 w-4 mr-2" />
          Aplicar Filtros y Comparar
        </Button>
      </div>
    </div>
  );
};