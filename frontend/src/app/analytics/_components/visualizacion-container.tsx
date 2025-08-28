"use client";

import React from "react";
import { BarChart3, Loader2, AlertCircle, TrendingUp, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Charts components (usando recharts como ejemplo)
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from "recharts";

import { useDatosVisualizacionQuery } from "@/lib/api/analytics";

interface VisualizacionContainerProps {
  grupoId: number;
  eventosSeleccionados: number[];
  tipoGrafico: string;
  clasificacion: string;
  fechaDesde?: string;
  fechaHasta?: string;
  generando: boolean;
}

export function VisualizacionContainer({
  grupoId,
  eventosSeleccionados,
  tipoGrafico,
  clasificacion,
  fechaDesde,
  fechaHasta,
  generando
}: VisualizacionContainerProps) {
  
  // Usar API real
  const { data, isLoading, error, refetch } = useDatosVisualizacionQuery({
    grupo_id: grupoId,
    evento_ids: eventosSeleccionados,
    clasificacion,
    fecha_desde: fechaDesde || undefined,
    fecha_hasta: fechaHasta || undefined,
    tipo_grafico: tipoGrafico
  }, !generando); // Solo hacer la llamada cuando no esté generando

  const datosVisualizacion = data?.data;

  const colors = [
    "#8884d8", "#82ca9d", "#ffc658", "#ff7300", "#ff0000",
    "#8dd1e1", "#d084d0", "#87d068", "#ffb347", "#87ceeb"
  ];

  if (generando || isLoading) {
    return (
      <Card>
        <CardContent className="p-12">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary mb-4" />
            <h3 className="text-lg font-medium mb-2">Generando Visualización</h3>
            <p className="text-sm text-muted-foreground">
              Procesando datos epidemiológicos...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Error al generar la visualización:</strong> {String(error)}
            </AlertDescription>
          </Alert>
          <div className="mt-4 text-center">
            <Button onClick={() => refetch()} variant="outline">
              Reintentar
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!datosVisualizacion?.datos || datosVisualizacion.datos.length === 0) {
    return (
      <Card>
        <CardContent className="p-12">
          <div className="text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <h3 className="text-lg font-medium mb-2">Sin datos para mostrar</h3>
            <p className="text-sm text-muted-foreground">
              No se encontraron datos con los filtros seleccionados.
              Intenta ajustar los parámetros de búsqueda.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const renderVisualizacion = () => {
    const datos = datosVisualizacion.datos;

    switch (tipoGrafico) {
      case "casos_por_edad":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={datos} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="rango" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="casos" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );

      case "torta_sexo":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={datos}
                dataKey="casos"
                nameKey="sexo"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => `${entry.sexo}: ${entry.casos}`}
              >
                {datos.map((_: unknown, index: number) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case "casos_mensual":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={datos} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="periodo" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="casos" 
                stroke="#8884d8" 
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case "corredor_endemico":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={datos} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="colorCasos" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="periodo" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="valor" 
                stroke="#8884d8" 
                fillOpacity={1} 
                fill="url(#colorCasos)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case "tabla":
        return (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">ID Caso</th>
                  <th className="text-left p-2">Nombre</th>
                  <th className="text-left p-2">Fecha</th>
                  <th className="text-left p-2">Clasificación</th>
                  <th className="text-left p-2">Ubicación</th>
                </tr>
              </thead>
              <tbody>
                {datos.slice(0, 10).map((item: Record<string, unknown>, index: number) => (
                  <tr key={index} className="border-b hover:bg-muted/20">
                    <td className="p-2 font-mono">{String(item.id || '')}</td>
                    <td className="p-2">{String(item.nombre || '')}</td>
                    <td className="p-2">{item.fecha ? new Date(String(item.fecha)).toLocaleDateString('es-ES') : 'N/A'}</td>
                    <td className="p-2">
                      <Badge variant="outline">{String(item.clasificacion || 'Sin clasificar')}</Badge>
                    </td>
                    <td className="p-2 text-muted-foreground">
                      {item.provincia && item.localidad ? `${String(item.localidad)}, ${String(item.provincia)}` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {datos.length > 10 && (
              <p className="text-center text-sm text-muted-foreground mt-4">
                Mostrando primeros 10 de {datos.length} registros
              </p>
            )}
          </div>
        );

      case "historicos":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={datos} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="categoria" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="valor" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <div className="text-center p-8">
            <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground opacity-50 mb-4" />
            <p className="text-sm text-muted-foreground">
              Tipo de gráfico no soportado: {tipoGrafico}
            </p>
          </div>
        );
    }
  };

  const getTituloGrafico = (tipo: string) => {
    const titulos: Record<string, string> = {
      casos_por_edad: "Casos por Grupo Etario",
      torta_sexo: "Distribución por Sexo",
      casos_mensual: "Evolución Mensual de Casos",
      tabla: "Tabla de Datos",
      historicos: "Datos Históricos",
      corredor_endemico: "Corredor Endémico"
    };
    return titulos[tipo] || "Visualización";
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              {getTituloGrafico(tipoGrafico)}
            </CardTitle>
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline">{datosVisualizacion.grupo}</Badge>
              <Badge variant="secondary">{datosVisualizacion.clasificacion}</Badge>
              <Badge variant="outline">{datosVisualizacion.total_casos} casos</Badge>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Exportar
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="grafico" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="grafico">Gráfico</TabsTrigger>
            <TabsTrigger value="metadatos">Información</TabsTrigger>
          </TabsList>
          
          <TabsContent value="grafico" className="mt-6">
            {renderVisualizacion()}
          </TabsContent>
          
          <TabsContent value="metadatos" className="mt-6">
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-medium">Eventos incluidos:</h4>
                <div className="mt-1 flex flex-wrap gap-1">
                  {datosVisualizacion.eventos.map((evento: string, index: number) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {evento}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium">Filtros aplicados:</h4>
                <div className="mt-1 text-muted-foreground">
                  {Object.entries(datosVisualizacion.filtros_aplicados).length > 0 ? (
                    Object.entries(datosVisualizacion.filtros_aplicados).map(([key, value]) => (
                      <div key={key}>• {key}: {String(value)}</div>
                    ))
                  ) : (
                    <div>• Sin filtros adicionales</div>
                  )}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium">Generado:</h4>
                <div className="text-muted-foreground">
                  {new Date(datosVisualizacion.fecha_generacion).toLocaleString('es-ES')}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}