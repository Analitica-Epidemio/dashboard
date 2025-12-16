"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  Users,
  Heart,
  AlertTriangle,
  TrendingUp,
  Stethoscope,
  FlaskConical,
  ClipboardList,
  Building2,
  ChevronRight,
  FileText,
  Loader2,
} from "lucide-react";
import { useQueries } from "@tanstack/react-query";

import { AppSidebar } from "@/features/layout/components/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api/client";
import {
  createYearFilter,
  extractTotalValue,
  type PeriodoFilter,
} from "@/features/metricas";

// --- Types ---
interface KpiProps {
  title: string;
  value: number | string;
  icon: React.ElementType;
  variant?: "default" | "warning" | "danger" | "success";
  description?: string;
  isLoading?: boolean;
}

interface VigilanciaCardProps {
  title: string;
  icon: React.ElementType;
  href: string;
  metrics: { label: string; value: string | number }[];
  trend?: { value: number; label: string };
  variant?: "default" | "warning" | "danger";
  isLoading?: boolean;
}

// --- Components ---
function KpiCard({
  title,
  value,
  icon: Icon,
  variant = "default",
  description,
  isLoading,
}: KpiProps) {
  const colorMap = {
    default: "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
    success:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400",
    warning:
      "bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400",
    danger: "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400",
  };

  return (
    <Card className="shadow-sm">
      <CardContent className="p-4 flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            {isLoading ? (
              <Skeleton className="h-7 w-20" />
            ) : (
              <span className="text-2xl font-bold tracking-tight">
                {typeof value === "number" ? value.toLocaleString() : value}
              </span>
            )}
          </div>
          {description && (
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        <div className={cn("p-2 rounded-lg", colorMap[variant])}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

function VigilanciaCard({
  title,
  icon: Icon,
  href,
  metrics,
  trend,
  variant = "default",
  isLoading,
}: VigilanciaCardProps) {
  const borderColors = {
    default: "border-l-blue-500",
    warning: "border-l-amber-500",
    danger: "border-l-rose-500",
  };

  return (
    <Card className={cn("shadow-sm border-l-4", borderColors[variant])}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          {trend && (
            <Badge
              variant={trend.value > 0 ? "destructive" : "secondary"}
              className="text-xs"
            >
              {trend.value > 0 ? "↑" : "↓"} {Math.abs(trend.value)}%{" "}
              {trend.label}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 mb-4">
          {metrics.map((m, i) => (
            <div key={i}>
              <p className="text-xs text-muted-foreground">{m.label}</p>
              {isLoading ? (
                <Skeleton className="h-6 w-16 mt-1" />
              ) : (
                <p className="text-lg font-semibold">
                  {typeof m.value === "number"
                    ? m.value.toLocaleString()
                    : m.value}
                </p>
              )}
            </div>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-between"
          asChild
        >
          <Link href={href}>
            Ver más <ChevronRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}

interface AlertItemProps {
  type: "warning" | "danger" | "info";
  title: string;
  description: string;
}

function AlertItem({ type, title, description }: AlertItemProps) {
  const config = {
    warning: {
      icon: AlertTriangle,
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-800",
    },
    danger: {
      icon: AlertTriangle,
      bg: "bg-rose-50",
      border: "border-rose-200",
      text: "text-rose-800",
    },
    info: {
      icon: Activity,
      bg: "bg-blue-50",
      border: "border-blue-200",
      text: "text-blue-800",
    },
  };
  const { icon: Icon, bg, border, text } = config[type];

  return (
    <div
      className={cn("flex items-start gap-3 p-3 rounded-lg border", bg, border)}
    >
      <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", text)} />
      <div>
        <p className={cn("font-medium text-sm", text)}>{title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
    </div>
  );
}

// --- Main Page ---
// Helper to create metric query config
function createMetricQuery(metric: string, periodo: PeriodoFilter) {
  return {
    queryKey: ["metricas", metric, periodo],
    queryFn: async () => {
      const response = await apiClient.POST("/api/v1/metricas/query", {
        body: {
          metric,
          dimensions: [],
          filters: { periodo },
        },
      });
      if (response.error) throw new Error(`Error fetching ${metric}`);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  };
}

export default function DashboardEjecutivoPage() {
  // Get current week
  const currentWeek = useMemo(() => {
    const now = new Date();
    const startOfYear = new Date(now.getFullYear(), 0, 1);
    const days = Math.floor(
      (now.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000)
    );
    return Math.ceil((days + startOfYear.getDay() + 1) / 7);
  }, []);

  const currentYear = new Date().getFullYear();
  const yearFilter = useMemo(
    () => createYearFilter(currentYear),
    [currentYear]
  );

  // Fetch both metrics in parallel using useQueries
  const [estudiadasQuery, positivasQuery] = useQueries({
    queries: [
      createMetricQuery("muestras_estudiadas", yearFilter),
      createMetricQuery("muestras_positivas", yearFilter),
    ],
  });

  // Derive metrics from query results
  const isLoading = estudiadasQuery.isLoading || positivasQuery.isLoading;
  const labMetrics = useMemo(() => {
    const estudiadas = extractTotalValue(estudiadasQuery.data);
    const positivas = extractTotalValue(positivasQuery.data);
    const positividad = estudiadas > 0 ? (positivas / estudiadas) * 100 : 0;

    return {
      muestrasEstudiadas: estudiadas,
      muestrasPositivas: positivas,
      positividad: Math.round(positividad * 10) / 10,
    };
  }, [estudiadasQuery.data, positivasQuery.data]);

  // Alerts based on real data
  const alertas: AlertItemProps[] = [
    {
      type: "info",
      title: "Sistema conectado al backend",
      description: `Datos en tiempo real del año ${currentYear}`,
    },
  ];

  if (labMetrics.muestrasPositivas > 0) {
    alertas.push({
      type: "warning",
      title: `${labMetrics.muestrasPositivas.toLocaleString()} muestras positivas`,
      description: `Positividad: ${labMetrics.positividad}% en ${currentYear}`,
    });
  }

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset className="bg-muted/10 h-screen overflow-hidden flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                Situación Epidemiológica
                {isLoading && (
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                )}
              </h1>
              <p className="text-sm text-muted-foreground">
                Semana Epidemiológica {currentWeek} · Año {currentYear}
              </p>
            </div>
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Exportar PDF
            </Button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-[1600px] mx-auto w-full">
          {/* Global KPIs */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <KpiCard
              title="Muestras Estudiadas"
              value={labMetrics.muestrasEstudiadas}
              icon={Activity}
              variant="default"
              description="Laboratorio - Acumulado anual"
              isLoading={isLoading}
            />
            <KpiCard
              title="Muestras Positivas"
              value={labMetrics.muestrasPositivas}
              icon={Users}
              variant="warning"
              description="Detecciones confirmadas"
              isLoading={isLoading}
            />
            <KpiCard
              title="Positividad"
              value={`${labMetrics.positividad}%`}
              icon={TrendingUp}
              variant={labMetrics.positividad > 30 ? "danger" : "success"}
              description="Tasa de positividad"
              isLoading={isLoading}
            />
            <KpiCard
              title="Hospitalizados"
              value="N/D"
              icon={Heart}
              variant="default"
              description="Vigilancia hospitalaria (próximamente)"
              isLoading={false}
            />
            <KpiCard
              title="Brotes Activos"
              value="N/D"
              icon={AlertTriangle}
              variant="default"
              description="Detección de brotes (próximamente)"
              isLoading={false}
            />
            <KpiCard
              title="Alertas"
              value="N/D"
              icon={TrendingUp}
              variant="default"
              description="Sistema de alertas (próximamente)"
              isLoading={false}
            />
          </section>

          {/* Vigilancia Summary Cards */}
          <section>
            <h2 className="text-lg font-semibold mb-4">
              Resumen por Tipo de Vigilancia
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <VigilanciaCard
                title="Vigilancia Clínica"
                icon={Stethoscope}
                href="/dashboard/vigilancia/clinica"
                metrics={[
                  { label: "Total Casos", value: "N/D" },
                  { label: "Tendencia", value: "N/D" },
                ]}
                variant="default"
                isLoading={false}
              />
              <VigilanciaCard
                title="Vigilancia por Laboratorio"
                icon={FlaskConical}
                href="/dashboard/vigilancia/laboratorio"
                metrics={[
                  { label: "Muestras", value: labMetrics.muestrasEstudiadas },
                  { label: "Positividad", value: `${labMetrics.positividad}%` },
                ]}
                variant={labMetrics.positividad > 30 ? "danger" : "warning"}
                isLoading={isLoading}
              />
              <VigilanciaCard
                title="Vigilancia Nominal"
                icon={ClipboardList}
                href="/dashboard/vigilancia/nominal"
                metrics={[
                  { label: "Casos", value: "N/D" },
                  { label: "Letalidad", value: "N/D" },
                ]}
                variant="default"
                isLoading={false}
              />
              <VigilanciaCard
                title="Vigilancia Hospitalaria"
                icon={Building2}
                href="/dashboard/vigilancia/hospitalaria"
                metrics={[
                  { label: "Internados", value: "N/D" },
                  { label: "UCI", value: "N/D" },
                ]}
                variant="default"
                isLoading={false}
              />
            </div>
          </section>

          {/* Status Section */}
          <section>
            <h2 className="text-lg font-semibold mb-4">Estado del Sistema</h2>
            <Card>
              <CardContent className="p-4 space-y-3">
                {alertas.map((alerta, i) => (
                  <AlertItem key={i} {...alerta} />
                ))}
              </CardContent>
            </Card>
          </section>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
