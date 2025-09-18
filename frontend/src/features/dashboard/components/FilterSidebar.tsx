/**
 * Sidebar de filtros persistente para análisis epidemiológico
 * Versión limpia enfocada solo en filtros de análisis
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar,
  MapPin,
  Users,
  Filter,
  RefreshCw
} from 'lucide-react';
import { GroupSelector } from './GroupSelector';
import { EventSelector } from './EventSelector';

interface FilterSidebarProps {
  groups: any[];
  selectedGroup: any;
  availableEvents: any[];
  selectedEvent: any;
  filters: any;
  onGroupChange: (group: any) => void;
  onEventChange: (event: any) => void;
  groupsLoading: boolean;
  eventsLoading: boolean;
  groupsError: Error | null;
  eventsError: Error | null;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  groups,
  selectedGroup,
  availableEvents,
  selectedEvent,
  filters,
  onGroupChange,
  onEventChange,
  groupsLoading,
  eventsLoading,
  groupsError,
  eventsError,
}) => {
  return (
    <div className="w-80 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto scroll-smooth">
        <div className="p-6">
        {/* Filtros Principales */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-3">
            <Filter className="h-5 w-5" />
            Filtros
          </h2>

          <div className="space-y-4">
              {/* Selector de Grupo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Grupo de Eventos
                </label>
                <GroupSelector
                  groups={groups}
                  selectedGroupId={filters.selectedGroupId}
                  onGroupChange={onGroupChange}
                  loading={groupsLoading}
                  error={groupsError?.message || null}
                />
              </div>

              {/* Selector de Evento */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Evento Específico
                </label>
                <EventSelector
                  events={availableEvents}
                  selectedEventId={filters.selectedEventId}
                  onEventChange={onEventChange}
                  disabled={!filters.selectedGroupId}
                  loading={eventsLoading}
                  error={eventsError?.message || null}
                  groupId={filters.selectedGroupId}
                />
              </div>

              {/* Filtros Adicionales */}
              <div className="space-y-3">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Calendar className="h-4 w-4 mr-2" />
                  Rango de Fechas
                </Button>
                
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <MapPin className="h-4 w-4 mr-2" />
                  Área Geográfica
                </Button>
                
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  Grupos Etarios
                </Button>
              </div>

              {/* Estado de Filtros Activos */}
              {(selectedGroup || selectedEvent) && (
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="p-3">
                    <div className="text-sm text-blue-800 font-medium mb-2">
                      Filtros Activos:
                    </div>
                    <div className="space-y-1">
                      {selectedGroup && (
                        <Badge variant="secondary" className="text-xs">
                          {selectedGroup.name}
                        </Badge>
                      )}
                      {selectedEvent && (
                        <Badge variant="secondary" className="text-xs">
                          {selectedEvent.name}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Acciones de Filtros */}
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" className="flex-1">
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Limpiar
                </Button>
                <Button variant="ghost" size="sm" className="flex-1">
                  Guardar
                </Button>
              </div>
            </div>
        </div>
        
      </div>
      </div>
    </div>
  );
};