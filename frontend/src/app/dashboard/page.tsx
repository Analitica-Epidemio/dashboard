"use client";

import { useState, useEffect } from "react";
import {
  Activity,
  Users,
  AlertCircle,
  CheckCircle,
  MapPin,
  BarChart3
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PopulationPyramid } from "@/features/dashboard/components/charts/PopulationPyramid";
import {
  getDashboardResumen,
  type DashboardResumen,
} from "@/lib/api/dashboard";

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
];

// Mapa de colores por clasificación
const CLASIFICACION_COLORS: Record<string, string> = {
  CONFIRMADOS: "#dc2626", // red-600
  SOSPECHOSOS: "#ea580c", // orange-600
  PROBABLES: "#f59e0b", // amber-500
  EN_ESTUDIO: "#3b82f6", // blue-500
  NEGATIVOS: "#65a30d", // lime-600
  DESCARTADOS: "#6b7280", // gray-500
  NOTIFICADOS: "#8b5cf6", // violet-500
  CON_RESULTADO_MORTAL: "#991b1b", // red-900
  SIN_RESULTADO_MORTAL: "#10b981", // green-500
  REQUIERE_REVISION: "#f97316", // orange-500
};

// Tabs custom con estilo moderno
interface ModernTabsProps {
  tabs: Array<{ id: string; label: string; icon: React.ReactNode }>;
  activeTab: string;
  onChange: (tab: string) => void;
}

function ModernTabs({ tabs, activeTab, onChange }: ModernTabsProps) {
  return (
    <div className="border-b border-border">
      <div className="flex gap-1 overflow-x-auto scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={cn(
              "relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all duration-200",
              "whitespace-nowrap border-b-2 -mb-[1px]",
              activeTab === tab.id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <span className="flex-shrink-0">{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// Componente reutilizable para tarjetas de métricas
interface MetricCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  colorClass?: string;
  subtitle?: string;
}

function MetricCard({ title, value, icon, colorClass = "text-blue-600", subtitle }: MetricCardProps) {
  return (
    <Card className="border-border/50 shadow-sm hover:shadow-md transition-shadow duration-200 p-0">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
        <CardTitle className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
          {title}
        </CardTitle>
        <div className={cn("p-1 rounded-md bg-muted/50", colorClass)}>
          {icon}
        </div>
      </CardHeader>
      <CardContent className="pb-3 px-3 pt-0">
        <div className={cn("text-lg font-bold tracking-tight", colorClass)}>
          {value.toLocaleString()}
        </div>
        {subtitle && (
          <p className="text-[11px] text-muted-foreground mt-0.5">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<DashboardResumen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("resumen");

  const tabsConfig = [
    { id: "resumen", label: "Resumen", icon: <BarChart3 className="h-4 w-4" /> },
    { id: "grupos", label: "Grupos", icon: <AlertCircle className="h-4 w-4" /> },
    { id: "demografico", label: "Demográfico", icon: <Users className="h-4 w-4" /> },
    { id: "geografico", label: "Geográfico", icon: <MapPin className="h-4 w-4" /> },
  ];

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const params = {
          fecha_desde: searchParams.get("fecha_desde") || undefined,
          fecha_hasta: searchParams.get("fecha_hasta") || undefined,
          grupo_id: searchParams.get("grupo_id")
            ? Number(searchParams.get("grupo_id"))
            : undefined,
          tipo_eno_id: searchParams.get("tipo_eno_id")
            ? Number(searchParams.get("tipo_eno_id"))
            : undefined,
          clasificacion: searchParams.get("clasificacion") || undefined,
          provincia_id: searchParams.get("provincia_id")
            ? Number(searchParams.get("provincia_id"))
            : undefined,
        };

        const resumen = await getDashboardResumen(params);
        setData(resumen);
        setError(null);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Error al cargar los datos del dashboard");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [searchParams]);

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>
            {error || "No hay datos disponibles"}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Validar que los datos tengan la estructura esperada
  if (
    !data.eventos_mas_tipicos ||
    !data.grupos_mas_tipicos ||
    !data.territorios_afectados
  ) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Error: La respuesta del servidor no tiene la estructura esperada.
            {JSON.stringify(data)}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Extraer todas las clasificaciones únicas del dataset
  const allClasificaciones = Array.from(
    new Set(
      data.eventos_mas_tipicos.flatMap((evento) =>
        Object.keys(evento.clasificaciones)
      )
    )
  ).sort();

  // Preparar datos para gráficos con todas las clasificaciones dinámicamente
  const eventosChartData = data.eventos_mas_tipicos.map((evento) => {
    const dataPoint: Record<string, string | number> = {
      nombre: evento.tipo_eno,
      total: evento.total,
    };

    // Agregar cada clasificación dinámicamente
    allClasificaciones.forEach((clasificacion) => {
      dataPoint[clasificacion] = evento.clasificaciones[clasificacion] || 0;
    });

    return dataPoint;
  });

  const gruposChartData = data.grupos_mas_tipicos.map((grupo) => ({
    name: grupo.grupo_eno,
    value: grupo.total,
  }));

  const territoriosChartData = data.territorios_afectados
    .slice(0, 10)
    .map((territorio) => ({
      nombre: territorio.nombre,
      total: territorio.total_eventos,
    }));

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold">Dashboard Epidemiológico</h1>
            </div>
          </div>
        </header>

        <main className="overflow-y-scroll flex-1 bg-muted">
          {/* Header Section */}
          <div className="bg-background border-b border-border">
            <div className="px-6 py-5">
              <h1 className="text-xl font-semibold">
                Dashboard Epidemiológico
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Análisis integral de eventos epidemiológicos
              </p>
            </div>

            <ModernTabs
              tabs={tabsConfig}
              activeTab={activeTab}
              onChange={setActiveTab}
            />
          </div>

          {/* Content Section */}
          <div className="p-6">
            {/* TAB: RESUMEN */}
            {activeTab === "resumen" && (
              <div className="space-y-6">
              {/* Tarjetas resumen mejoradas */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                <MetricCard
                  title="Total Eventos"
                  value={data.tabla_resumen.total_eventos}
                  icon={<Activity className="h-4 w-4" />}
                  colorClass="text-blue-600"
                  subtitle="Eventos registrados"
                />
                <MetricCard
                  title="Confirmados"
                  value={data.tabla_resumen.total_confirmados}
                  icon={<CheckCircle className="h-4 w-4" />}
                  colorClass="text-red-600"
                  subtitle={`${((data.tabla_resumen.total_confirmados / data.tabla_resumen.total_eventos) * 100).toFixed(1)}% del total`}
                />
                <MetricCard
                  title="Sospechosos"
                  value={data.tabla_resumen.total_sospechosos}
                  icon={<AlertCircle className="h-4 w-4" />}
                  colorClass="text-orange-600"
                  subtitle={`${((data.tabla_resumen.total_sospechosos / data.tabla_resumen.total_eventos) * 100).toFixed(1)}% del total`}
                />
                <MetricCard
                  title="Personas Afectadas"
                  value={data.tabla_resumen.total_personas_afectadas}
                  icon={<Users className="h-4 w-4" />}
                  colorClass="text-purple-600"
                  subtitle="Individuos únicos"
                />
              </div>

              {/* Período de datos */}
              {data.tabla_resumen.fecha_primer_evento &&
                data.tabla_resumen.fecha_ultimo_evento && (
                  <Card className="border-border/50 shadow-sm">
                    <CardHeader>
                      <CardTitle className="text-sm">Período de Datos</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        Desde{" "}
                        <span className="font-medium text-foreground">
                          {data.tabla_resumen.fecha_primer_evento}
                        </span>{" "}
                        hasta{" "}
                        <span className="font-medium text-foreground">
                          {data.tabla_resumen.fecha_ultimo_evento}
                        </span>
                      </p>
                    </CardContent>
                  </Card>
                )}

              {/* Gráfico principal de eventos */}
              <Card className="border-border/50 shadow-sm">
                <CardHeader>
                  <CardTitle>Eventos por Tipo</CardTitle>
                  <CardDescription>
                    Distribución de clasificaciones por tipo de evento
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={eventosChartData} margin={{ bottom: 80 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="nombre"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        interval={0}
                        tick={{ fontSize: 10 }}
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend wrapperStyle={{ paddingTop: "10px" }} />
                      {allClasificaciones.map((clasificacion) => (
                        <Bar
                          key={clasificacion}
                          dataKey={clasificacion}
                          stackId="a"
                          fill={CLASIFICACION_COLORS[clasificacion] || "#94a3b8"}
                          name={clasificacion.replace(/_/g, " ")}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Tabla detallada de eventos */}
              <Card className="border-border/50 shadow-sm">
                <CardHeader>
                  <CardTitle>Detalle de Eventos por Clasificación</CardTitle>
                  <CardDescription>
                    Desglose completo de {data.eventos_mas_tipicos.length} tipos de eventos
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-muted">
                        <tr className="border-b">
                          <th className="text-left p-3 font-semibold sticky left-0 bg-muted z-10">Tipo de Evento</th>
                          <th className="text-right p-3 font-semibold">Total</th>
                          {allClasificaciones.map((clasificacion) => (
                            <th key={clasificacion} className="text-right p-3 font-semibold whitespace-nowrap">
                              {clasificacion.replace(/_/g, " ")}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.eventos_mas_tipicos.map((evento, idx) => (
                          <tr key={idx} className="border-b hover:bg-muted/50 transition-colors">
                            <td className="p-3 font-medium sticky left-0 bg-background hover:bg-muted/50 z-10">{evento.tipo_eno}</td>
                            <td className="text-right p-3 font-semibold">
                              {evento.total.toLocaleString()}
                            </td>
                            {allClasificaciones.map((clasificacion) => {
                              const valor = evento.clasificaciones[clasificacion] || 0;
                              const color = CLASIFICACION_COLORS[clasificacion];
                              return (
                                <td
                                  key={clasificacion}
                                  className="text-right p-3 font-medium whitespace-nowrap"
                                  style={{ color: valor > 0 ? color : undefined }}
                                >
                                  {valor > 0 ? valor.toLocaleString() : "-"}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
              </div>
            )}

            {/* TAB: GRUPOS */}
            {activeTab === "grupos" && (
              <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Desglose detallado */}
                <Card className="border-border/50 shadow-sm">
                  <CardHeader>
                    <CardTitle>Desglose por Grupo</CardTitle>
                    <CardDescription>Tipos de eventos en cada grupo</CardDescription>
                  </CardHeader>
                  <CardContent className="max-h-[600px] overflow-y-auto">
                    <div className="space-y-6">
                      {data.grupos_mas_tipicos.map((grupo, idx) => (
                        <div key={idx} className="border rounded-lg p-4 bg-muted/20">
                          <div className="flex justify-between items-center mb-3">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                              <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                              />
                              {grupo.grupo_eno}
                            </h3>
                            <div className="text-right">
                              <div className="text-2xl font-bold text-primary">
                                {grupo.total.toLocaleString()}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {((grupo.total / data.tabla_resumen.total_eventos) * 100).toFixed(1)}% del total
                              </div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                            {grupo.tipos.map((tipo, tidx) => (
                              <div
                                key={tidx}
                                className="bg-background border rounded-md p-2 flex justify-between items-center hover:bg-muted/50 transition-colors"
                              >
                                <span className="text-sm truncate mr-2" title={tipo.tipo}>
                                  {tipo.tipo}
                                </span>
                                <span className="text-sm font-semibold">
                                  {tipo.total}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Gráfico de pie */}
                <Card className="border-border/50 shadow-sm">
                  <CardHeader>
                    <CardTitle>Distribución General</CardTitle>
                    <CardDescription>Por grupos epidemiológicos</CardDescription>
                  </CardHeader>
                  <CardContent className="flex items-center justify-center h-[600px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={gruposChartData}
                          cx="50%"
                          cy="50%"
                          labelLine={true}
                          label={(entry: { name: string; value: number }) => `${entry.name}: ${entry.value}`}
                          outerRadius={120}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {gruposChartData.map((_, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
              </div>
            )}

            {/* TAB: DEMOGRÁFICO */}
            {activeTab === "demografico" && (
              <div className="space-y-6">
              {data.piramide_poblacional.length > 0 ? (
                <Card className="border-border/50 shadow-sm">
                  <CardHeader>
                    <CardTitle>Pirámide Poblacional de Eventos</CardTitle>
                    <CardDescription>
                      Distribución por edad y sexo de {data.tabla_resumen.total_personas_afectadas.toLocaleString()} personas afectadas
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-center">
                      <PopulationPyramid
                        data={data.piramide_poblacional}
                        width={800}
                        height={500}
                      />
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-border/50 shadow-sm">
                  <CardContent className="py-12">
                    <div className="text-center text-muted-foreground">
                      <Users className="h-12 w-12 mx-auto mb-4 opacity-20" />
                      <p>No hay datos demográficos disponibles para el período seleccionado</p>
                    </div>
                  </CardContent>
                </Card>
              )}
              </div>
            )}

            {/* TAB: GEOGRÁFICO */}
            {activeTab === "geografico" && (
              <div className="space-y-6">
              {territoriosChartData.length > 0 ? (
                <Card className="border-border/50 shadow-sm">
                  <CardHeader>
                    <CardTitle>Distribución Geográfica</CardTitle>
                    <CardDescription>
                      Top {territoriosChartData.length} provincias por número de eventos
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={500}>
                      <BarChart data={territoriosChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis
                          dataKey="nombre"
                          type="category"
                          width={180}
                          tick={{ fontSize: 12 }}
                        />
                        <Tooltip
                          formatter={(value: number) => [value.toLocaleString(), "Total Eventos"]}
                        />
                        <Bar dataKey="total" fill="#3b82f6" name="Total Eventos" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-border/50 shadow-sm">
                  <CardContent className="py-12">
                    <div className="text-center text-muted-foreground">
                      <MapPin className="h-12 w-12 mx-auto mb-4 opacity-20" />
                      <p>No hay datos geográficos disponibles para el período seleccionado</p>
                    </div>
                  </CardContent>
                </Card>
              )}
              </div>
            )}
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
