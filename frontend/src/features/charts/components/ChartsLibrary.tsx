"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  BookOpen,
  Code2,
  Eye,
  Copy,
  Settings,
  Filter,
  Search,
  BarChart3, 
  PieChart, 
  LineChart, 
  Map, 
  TrendingUp,
  Grid,
  Loader2 
} from "lucide-react";
import { toast } from "sonner";
import { useChartTemplates } from "../services/api";
import { ChartComponent } from "./ChartComponent";

interface ChartTemplate {
  id: number;
  codigo: string;
  nombre: string;
  descripcion?: string;
  categoria: string;
  tipo_visualizacion: string;
  filtros_opcionales: string[];
  parametros_disponibles: Record<string, any>;
  parametros_default: Record<string, any>;
}

export function ChartsLibrary() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [previewChart, setPreviewChart] = useState<string>("");
  const [previewFilters, setPreviewFilters] = useState({
    tipo_eno: "DENGUE",
    fecha_inicio: "",
    fecha_fin: ""
  });

  // Fetch all chart templates
  const { data: templatesResponse, isLoading: templatesLoading } = useChartTemplates();
  const chartTemplates: ChartTemplate[] = templatesResponse?.data || [];

  // Filter templates
  const filteredTemplates = chartTemplates.filter(template => {
    const matchesSearch = template.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.descripcion?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = selectedCategory === "all" || template.categoria === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = ["all", ...Array.from(new Set(chartTemplates.map(t => t.categoria)))];

  const getVisualizationIcon = (type: string) => {
    switch (type) {
      case "line": return LineChart;
      case "bar": return BarChart3;
      case "pie": return PieChart;
      case "map": return Map;
      case "metric": return TrendingUp;
      case "area": return TrendingUp;
      case "heatmap": return Grid;
      default: return BarChart3;
    }
  };

  const getCategoryColor = (categoria: string) => {
    switch (categoria) {
      case "epidemiological": return "bg-blue-100 text-blue-800";
      case "demographic": return "bg-green-100 text-green-800";
      case "geographic": return "bg-purple-100 text-purple-800";
      case "temporal": return "bg-orange-100 text-orange-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const handleCopyUsage = (chartCode: string) => {
    const usageCode = `import { ChartComponent } from '@/features/charts/components/ChartComponent';

// Uso básico
<ChartComponent 
  chartCode="${chartCode}"
  filtros={{
    tipo_eno: "DENGUE",
    fecha_inicio: "2024-01-01",
    fecha_fin: "2024-12-31"
  }}
/>

// Con hook
import { useChart } from '@/features/charts/hooks/useChart';

const { data, isLoading, error } = useChart({
  chartCode: "${chartCode}",
  filtros: { tipo_eno: "DENGUE" }
});`;

    navigator.clipboard.writeText(usageCode);
    toast.success("Código de uso copiado al portapapeles");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 mb-2">
          <BookOpen className="h-6 w-6" />
          <h1 className="text-3xl font-bold">Biblioteca de Charts</h1>
        </div>
        <p className="text-muted-foreground">
          Componentes de visualización reutilizables para dashboards epidemiológicos.
          Previsualiza, configura y copia el código para usar en tus dashboards.
        </p>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Search className="h-5 w-5" />
            <CardTitle>Explorar Charts</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Label htmlFor="search">Buscar</Label>
              <Input
                id="search"
                placeholder="Buscar por nombre, código o descripción..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="category">Categoría</Label>
              <select
                id="category"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>
                    {cat === "all" ? "Todas las categorías" : cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="gallery" className="space-y-4">
        <TabsList>
          <TabsTrigger value="gallery">📚 Galería</TabsTrigger>
          <TabsTrigger value="preview">👁️ Vista Previa</TabsTrigger>
          <TabsTrigger value="documentation">📖 Documentación</TabsTrigger>
        </TabsList>

        <TabsContent value="gallery" className="space-y-4">
          {templatesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Cargando biblioteca de charts...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTemplates.map((template) => {
                const IconComponent = getVisualizationIcon(template.tipo_visualizacion);
                
                return (
                  <Card key={template.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <IconComponent className="h-5 w-5 text-primary" />
                          <CardTitle className="text-lg">{template.nombre}</CardTitle>
                        </div>
                        <Badge className={getCategoryColor(template.categoria)}>
                          {template.categoria}
                        </Badge>
                      </div>
                      <CardDescription className="text-sm">
                        {template.descripcion}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center text-sm text-muted-foreground space-x-4">
                          <span>Código: {template.codigo}</span>
                        </div>
                        <div className="flex items-center text-sm text-muted-foreground space-x-4">
                          <span>Tipo: {template.tipo_visualizacion}</span>
                          <span>•</span>
                          <span>{template.filtros_opcionales.length} filtros</span>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => setPreviewChart(template.codigo)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Preview
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleCopyUsage(template.codigo)}
                          >
                            <Code2 className="h-4 w-4 mr-1" />
                            Código
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="preview" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Vista Previa de Chart</CardTitle>
                  <CardDescription>
                    Configura filtros y ve el chart en acción
                  </CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Label htmlFor="chart-select">Chart:</Label>
                  <select
                    id="chart-select"
                    className="flex h-10 w-[200px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={previewChart}
                    onChange={(e) => setPreviewChart(e.target.value)}
                  >
                    <option value="">Selecciona un chart</option>
                    {chartTemplates.map(t => (
                      <option key={t.codigo} value={t.codigo}>
                        {t.nombre}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {previewChart ? (
                <div className="space-y-4">
                  {/* Filtros de prueba */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
                    <div>
                      <Label>Tipo ENO</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={previewFilters.tipo_eno}
                        onChange={(e) => setPreviewFilters(prev => ({ ...prev, tipo_eno: e.target.value }))}
                      >
                        <option value="DENGUE">Dengue</option>
                        <option value="TUBERCULOSIS">Tuberculosis</option>
                        <option value="SIFILIS">Sífilis</option>
                      </select>
                    </div>
                    <div>
                      <Label>Fecha Inicio</Label>
                      <Input
                        type="date"
                        value={previewFilters.fecha_inicio}
                        onChange={(e) => setPreviewFilters(prev => ({ ...prev, fecha_inicio: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label>Fecha Fin</Label>
                      <Input
                        type="date"
                        value={previewFilters.fecha_fin}
                        onChange={(e) => setPreviewFilters(prev => ({ ...prev, fecha_fin: e.target.value }))}
                      />
                    </div>
                  </div>

                  {/* Chart Preview */}
                  <ChartComponent
                    chartCode={previewChart}
                    filtros={previewFilters}
                    autoLoad={true}
                    className="min-h-[400px]"
                  />
                </div>
              ) : (
                <div className="flex items-center justify-center py-12 text-muted-foreground">
                  <div className="text-center">
                    <Eye className="h-12 w-12 mx-auto mb-4" />
                    <p>Selecciona un chart para previsualizar</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documentation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Documentación de Uso</CardTitle>
              <CardDescription>
                Cómo usar los charts en tus dashboards
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">1. Uso Básico del Componente</h3>
                <pre className="bg-muted p-4 rounded text-sm overflow-x-auto">
{`import { ChartComponent } from '@/features/charts/components/ChartComponent';

<ChartComponent 
  chartCode="curva_epidemiologica"
  filtros={{
    tipo_eno: "DENGUE",
    fecha_inicio: "2024-01-01",
    fecha_fin: "2024-12-31"
  }}
  title="Mi Chart Personalizado"
  className="h-96"
/>`}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. Uso con Hook</h3>
                <pre className="bg-muted p-4 rounded text-sm overflow-x-auto">
{`import { useChart } from '@/features/charts/hooks/useChart';

function MiDashboard() {
  const { data, isLoading, error } = useChart({
    chartCode: "distribucion_geografica",
    filtros: { tipo_eno: "TUBERCULOSIS" },
    autoLoad: true
  });

  if (isLoading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return <div>{/* Renderizar data */}</div>;
}`}
                </pre>
              </div>

              <div>
                <h3 className="font-semibold mb-2">3. Múltiples Charts</h3>
                <pre className="bg-muted p-4 rounded text-sm overflow-x-auto">
{`import { useMultipleCharts } from '@/features/charts/hooks/useChart';

const { chartsData, loadingCharts } = useMultipleCharts({
  charts: [
    { code: "curva_epidemiologica", filtros: { tipo_eno: "DENGUE" } },
    { code: "distribucion_geografica", filtros: { tipo_eno: "DENGUE" } },
    { code: "tasa_letalidad", filtros: { tipo_eno: "DENGUE" } }
  ]
});`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}