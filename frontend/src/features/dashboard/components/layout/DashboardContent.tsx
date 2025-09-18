"use client";

import { EpidemiologyNavigationCard } from "./NavigationLink";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, Loader2, BarChart3, Activity } from "lucide-react";
import { ChartCard } from "../charts/ChartComponents";
import { EpidemiologicalChartsSection } from "../charts";
import { EventSelector, GroupSelector } from "../selectors";
import { useDashboardFilters } from "../../hooks/useDashboardFilters";

export function DashboardContent() {
  const {
    groups,
    groupsLoading,
    groupsError,
    availableEvents,
    eventsLoading,
    eventsError,
    chartData,
    chartDataLoading,
    chartDataError,
    selectedGroup,
    selectedEvent,
    filters,
    setSelectedGroup,
    setSelectedEvent,
  } = useDashboardFilters();

  return (
    <div className="space-y-6">
      {/* Filters Section */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros de Búsqueda</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <GroupSelector
              groups={groups}
              selectedGroupId={filters.selectedGroupId}
              onGroupChange={setSelectedGroup}
              loading={groupsLoading}
              error={groupsError}
            />
            <EventSelector
              events={availableEvents}
              selectedEventId={filters.selectedEventId}
              onEventChange={setSelectedEvent}
              disabled={!filters.selectedGroupId}
              loading={eventsLoading}
              error={eventsError}
            />
          </div>
        </CardContent>
      </Card>

      {/* Epidemiological Analysis Navigation */}
      <EpidemiologyNavigationCard />

      {/* Selected Information */}
      {selectedGroup && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">
                <span className="font-medium">Grupo seleccionado:</span>{" "}
                {selectedGroup.name}
              </div>
              {selectedEvent && (
                <div className="text-sm text-muted-foreground">
                  <span className="font-medium">Evento seleccionado:</span>{" "}
                  {selectedEvent.name}
                  {selectedEvent.description && (
                    <span className="block text-xs mt-1">
                      {selectedEvent.description}
                    </span>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Sections - Only show when event is selected */}
      {selectedEvent && (
        <Tabs defaultValue="standard-charts" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger
              value="standard-charts"
              className="flex items-center gap-2"
            >
              <BarChart3 className="h-4 w-4" />
              Gráficos Estándar
            </TabsTrigger>
            <TabsTrigger
              value="epidemiological-analysis"
              className="flex items-center gap-2"
            >
              <Activity className="h-4 w-4" />
              Análisis Epidemiológico
            </TabsTrigger>
          </TabsList>

          <TabsContent value="standard-charts" className="space-y-4">
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold">
                Análisis de Datos - {selectedEvent.name}
              </h2>
              {chartDataLoading && <Loader2 className="h-5 w-5 animate-spin" />}
            </div>

            {chartDataError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {chartDataError.message ||
                    "Error al cargar datos de gráficos"}
                </AlertDescription>
              </Alert>
            )}

            {chartDataLoading && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {[1, 2, 3, 4].map((n) => (
                  <Card key={n}>
                    <CardHeader>
                      <Skeleton className="h-6 w-3/4" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-[300px] w-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {chartData.length > 0 && !chartDataLoading && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {chartData.map((chart, index) => (
                  <ChartCard key={index} chartData={chart} />
                ))}
              </div>
            )}

            {chartData.length === 0 && !chartDataLoading && !chartDataError && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p>No hay datos de gráficos disponibles para este evento</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="epidemiological-analysis">
            <EpidemiologicalChartsSection
              selectedGroup={selectedGroup}
              selectedEvent={selectedEvent}
              filters={filters}
            />
          </TabsContent>
        </Tabs>
      )}

      {/* Empty States */}
      {!selectedEvent && filters.selectedGroupId && !eventsLoading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              <p>Selecciona un evento para ver los gráficos de análisis</p>
            </div>
          </CardContent>
        </Card>
      )}

      {!filters.selectedGroupId && !groupsLoading && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              <p>Selecciona un grupo para comenzar</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
