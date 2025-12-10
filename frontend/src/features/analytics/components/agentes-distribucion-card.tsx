"use client";

/**
 * AgentesDistribucionCard Component
 *
 * Displays distribution of etiological agents by week as a stacked bar chart
 * and optionally by age group.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { AgenteSemanaData, AgenteEdadData } from "../api";

interface AgentesDistribucionCardProps {
  title: string;
  description?: string;
  porSemana: AgenteSemanaData[];
  porEdad?: AgenteEdadData[];
  className?: string;
}

// Color palette for agents
const AGENT_COLORS = [
  "#3b82f6", // blue-500
  "#ef4444", // red-500
  "#22c55e", // green-500
  "#f59e0b", // amber-500
  "#8b5cf6", // violet-500
  "#ec4899", // pink-500
  "#06b6d4", // cyan-500
  "#84cc16", // lime-500
  "#f97316", // orange-500
  "#6366f1", // indigo-500
];

/**
 * Transform weekly data to chart format
 */
function transformWeeklyData(data: AgenteSemanaData[]) {
  // Group by week
  const weekMap = new Map<number, Record<string, number>>();
  const agents = new Set<string>();

  data.forEach((d) => {
    agents.add(d.agente_nombre);
    const weekData = weekMap.get(d.semana_epidemiologica) || {};
    weekData[d.agente_nombre] = d.positivas;
    weekMap.set(d.semana_epidemiologica, weekData);
  });

  // Convert to array sorted by week
  const result = Array.from(weekMap.entries())
    .sort(([a], [b]) => a - b)
    .map(([semana, agentes]) => ({
      semana: `SE ${semana}`,
      ...agentes,
    }));

  return { chartData: result, agents: Array.from(agents) };
}

/**
 * Transform age data to chart format
 */
function transformAgeData(data: AgenteEdadData[]) {
  // Group by age group
  const ageMap = new Map<string, Record<string, number>>();
  const agents = new Set<string>();

  data.forEach((d) => {
    agents.add(d.agente_nombre);
    const ageData = ageMap.get(d.grupo_etario) || {};
    ageData[d.agente_nombre] = d.positivas;
    ageMap.set(d.grupo_etario, ageData);
  });

  // Convert to array
  const result = Array.from(ageMap.entries()).map(([grupo, agentes]) => ({
    grupo_etario: grupo,
    ...agentes,
  }));

  return { chartData: result, agents: Array.from(agents) };
}

export function AgentesDistribucionCard({
  title,
  description,
  porSemana,
  porEdad,
  className,
}: AgentesDistribucionCardProps) {
  const weeklyTransformed = transformWeeklyData(porSemana);
  const ageTransformed = porEdad ? transformAgeData(porEdad) : null;

  // Calculate totals
  const totalPositivas = porSemana.reduce((acc, d) => acc + d.positivas, 0);
  const totalEstudiadas = porSemana.reduce((acc, d) => acc + d.estudiadas, 0);
  const tasaGlobal = totalEstudiadas > 0 ? (totalPositivas / totalEstudiadas * 100).toFixed(1) : "0";

  const showTabs = porEdad && porEdad.length > 0;

  const renderBarChart = (
    chartData: Array<Record<string, unknown>>,
    xKey: string,
    agents: string[]
  ) => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length > 0) {
              const total = payload.reduce((acc, p) => acc + (Number(p.value) || 0), 0);
              return (
                <div className="bg-white p-3 border rounded-lg shadow-lg">
                  <p className="font-semibold mb-2">{label}</p>
                  <div className="space-y-1 text-sm">
                    {payload.map((p, i) => (
                      <p key={i} style={{ color: p.color }}>
                        {p.name}: {p.value} ({total > 0 ? ((Number(p.value) / total) * 100).toFixed(0) : 0}%)
                      </p>
                    ))}
                    <hr className="my-1" />
                    <p className="font-medium">Total: {total}</p>
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend wrapperStyle={{ fontSize: "12px" }} />
        {agents.map((agent, i) => (
          <Bar
            key={agent}
            dataKey={agent}
            stackId="a"
            fill={AGENT_COLORS[i % AGENT_COLORS.length]}
            name={agent}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-sm">
              {totalPositivas} positivas
            </Badge>
            <Badge variant="outline" className="text-sm">
              {tasaGlobal}% positividad
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {porSemana.length === 0 ? (
          <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
            <p className="text-muted-foreground">No hay datos disponibles</p>
          </div>
        ) : showTabs ? (
          <Tabs defaultValue="semana">
            <TabsList className="mb-4">
              <TabsTrigger value="semana">Por Semana</TabsTrigger>
              <TabsTrigger value="edad">Por Edad</TabsTrigger>
            </TabsList>
            <TabsContent value="semana">
              {renderBarChart(weeklyTransformed.chartData, "semana", weeklyTransformed.agents)}
            </TabsContent>
            <TabsContent value="edad">
              {ageTransformed && renderBarChart(
                ageTransformed.chartData,
                "grupo_etario",
                ageTransformed.agents
              )}
            </TabsContent>
          </Tabs>
        ) : (
          renderBarChart(weeklyTransformed.chartData, "semana", weeklyTransformed.agents)
        )}
      </CardContent>
    </Card>
  );
}
