"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { ArrowUpDown, Search, Bug, FileText } from "lucide-react";
import { $api } from "@/lib/api/client";
import type { components } from "@/lib/api/types";

// Types from OpenAPI
type TipoEnoInfo = components["schemas"]["EnfermedadInfo"];
type AgenteEtiologicoInfo = components["schemas"]["AgenteEtiologicoInfo"];
type AgentesCategoriasResponse = components["schemas"]["AgentesCategoriasResponse"];

// Sortable column header component
function SortableHeader({
  label,
  field,
  currentField,
  onSort,
}: {
  label: string;
  field: string;
  currentField: string;
  currentOrder: string;
  onSort: (field: string) => void;
}) {
  const isActive = currentField === field;
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8 data-[state=open]:bg-accent"
      onClick={() => onSort(field)}
    >
      {label}
      <ArrowUpDown
        className={`ml-2 h-4 w-4 ${isActive ? "text-primary" : "text-muted-foreground"}`}
      />
    </Button>
  );
}

// Tipos ENO Tab
function TiposEnoTab() {
  const [page, setPage] = useState(1);
  const [ordenarPor, setOrdenarPor] = useState("total_casos");
  const [orden, setOrden] = useState("desc");
  const [busqueda, setBusqueda] = useState("");
  const perPage = 20;

  const { data, isLoading, isError } = $api.useQuery(
    "get",
    "/api/v1/tiposEno/",
    {
      params: {
        query: {
          page,
          per_page: perPage,
          ordenar_por: ordenarPor,
          orden,
          nombre: busqueda || undefined,
        },
      },
    }
  );

  const handleSort = (field: string) => {
    if (ordenarPor === field) {
      setOrden(orden === "asc" ? "desc" : "asc");
    } else {
      setOrdenarPor(field);
      setOrden("desc");
    }
    setPage(1);
  };

  if (isError) {
    return (
      <div className="text-center py-8 text-destructive">
        Error cargando tipos de eventos
      </div>
    );
  }

  const tipos = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre..."
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <div className="text-sm text-muted-foreground">
          {meta?.total ?? 0} tipos de eventos
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">ID</TableHead>
              <TableHead>
                <SortableHeader
                  label="Nombre"
                  field="nombre"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Grupos</TableHead>
              <TableHead className="text-right">
                <SortableHeader
                  label="Total Casos"
                  field="total_casos"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Skeleton className="h-4 w-8" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-48" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-16 ml-auto" />
                  </TableCell>
                </TableRow>
              ))
            ) : tipos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  No se encontraron tipos de eventos
                </TableCell>
              </TableRow>
            ) : (
              tipos.map((tipo: TipoEnoInfo) => (
                <TableRow key={tipo.id}>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {tipo.id}
                  </TableCell>
                  <TableCell className="font-medium">{tipo.nombre}</TableCell>
                  <TableCell>
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                      {tipo.codigo || "-"}
                    </code>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {(tipo.grupos ?? []).map((g) => (
                        <Badge key={g.id} variant="outline" className="text-xs">
                          {g.nombre}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {tipo.total_casos.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {meta && meta.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/30">
            <p className="text-xs text-muted-foreground">
              Mostrando {(page - 1) * perPage + 1}-
              {Math.min(page * perPage, meta.total)} de {meta.total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= meta.total_pages}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Agentes Tab
function AgentesTab() {
  const [page, setPage] = useState(1);
  const [ordenarPor, setOrdenarPor] = useState("eventos_positivos");
  const [orden, setOrden] = useState("desc");
  const [busqueda, setBusqueda] = useState("");
  const [categoriaFiltro, setCategoriaFiltro] = useState("todas");
  const [grupoFiltro, setGrupoFiltro] = useState("todos");
  const perPage = 20;

  const { data: categoriasData } = $api.useQuery(
    "get",
    "/api/v1/agentes/categorias"
  );

  const { data, isLoading, isError } = $api.useQuery(
    "get",
    "/api/v1/agentes/",
    {
      params: {
        query: {
          page,
          per_page: perPage,
          ordenar_por: ordenarPor,
          orden,
          busqueda: busqueda || undefined,
          categoria: categoriaFiltro !== "todas" ? categoriaFiltro : undefined,
          grupo: grupoFiltro !== "todos" ? grupoFiltro : undefined,
        },
      },
    }
  );

  const handleSort = (field: string) => {
    if (ordenarPor === field) {
      setOrden(orden === "asc" ? "desc" : "asc");
    } else {
      setOrdenarPor(field);
      setOrden("desc");
    }
    setPage(1);
  };

  if (isError) {
    return (
      <div className="text-center py-8 text-destructive">
        Error cargando agentes etiológicos
      </div>
    );
  }

  const agentes = data?.data ?? [];
  const meta = data?.meta;
  const catResponse = categoriasData as AgentesCategoriasResponse | undefined;
  const categorias = catResponse?.categorias ?? [];
  const grupos = catResponse?.grupos ?? [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre o código..."
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={categoriaFiltro}
          onValueChange={(v) => {
            setCategoriaFiltro(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Categoría" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todas">Todas las categorías</SelectItem>
            {categorias.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={grupoFiltro}
          onValueChange={(v) => {
            setGrupoFiltro(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Grupo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los grupos</SelectItem>
            {grupos.map((grupo) => (
              <SelectItem key={grupo} value={grupo}>
                {grupo.charAt(0).toUpperCase() + grupo.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="text-sm text-muted-foreground">
          {meta?.total ?? 0} agentes
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <SortableHeader
                  label="Nombre"
                  field="nombre"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Categoría</TableHead>
              <TableHead>Grupo</TableHead>
              <TableHead className="text-right">
                <SortableHeader
                  label="Total"
                  field="total_eventos"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
              <TableHead className="text-right">
                <SortableHeader
                  label="Positivos"
                  field="eventos_positivos"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
              <TableHead className="text-right">
                <SortableHeader
                  label="Tasa %"
                  field="tasa_positividad"
                  currentField={ordenarPor}
                  currentOrder={orden}
                  onSort={handleSort}
                />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Skeleton className="h-4 w-40" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-12 ml-auto" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-12 ml-auto" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-12 ml-auto" />
                  </TableCell>
                </TableRow>
              ))
            ) : agentes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8">
                  No se encontraron agentes etiológicos
                </TableCell>
              </TableRow>
            ) : (
              agentes.map((agente: AgenteEtiologicoInfo) => (
                <TableRow key={agente.id}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {agente.nombre_corto}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {agente.nombre}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                      {agente.codigo}
                    </code>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        agente.categoria === "virus"
                          ? "default"
                          : agente.categoria === "bacteria"
                            ? "secondary"
                            : "outline"
                      }
                      className="text-xs"
                    >
                      {agente.categoria}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{agente.grupo}</TableCell>
                  <TableCell className="text-right font-mono">
                    {agente.total_eventos.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-green-600">
                    {agente.eventos_positivos.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`font-mono ${agente.tasa_positividad > 50
                          ? "text-red-600"
                          : agente.tasa_positividad > 20
                            ? "text-amber-600"
                            : "text-muted-foreground"
                        }`}
                    >
                      {agente.tasa_positividad.toFixed(1)}%
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {meta && meta.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3 bg-muted/30">
            <p className="text-xs text-muted-foreground">
              Mostrando {(page - 1) * perPage + 1}-
              {Math.min(page * perPage, meta.total)} de {meta.total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page <= 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= meta.total_pages}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Main Page
export default function CatalogosPage() {
  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header */}
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-lg font-semibold">Catálogos</h1>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-y-scroll bg-muted/40">
          <Tabs defaultValue="tipos-eno" className="space-y-4">
            <TabsList>
              <TabsTrigger value="tipos-eno" className="gap-2">
                <FileText className="h-4 w-4" />
                Tipos de Eventos (ENO)
              </TabsTrigger>
              <TabsTrigger value="agentes" className="gap-2">
                <Bug className="h-4 w-4" />
                Agentes Etiológicos
              </TabsTrigger>
            </TabsList>

            <TabsContent value="tipos-eno">
              <div className="border border-border bg-background rounded-lg overflow-hidden">
                <div className="p-4 border-b border-border">
                  <h2 className="font-medium">Tipos de Eventos Epidemiológicos</h2>
                  <p className="text-sm text-muted-foreground">
                    Catálogo de eventos de notificación obligatoria con cantidad de casos registrados
                  </p>
                </div>
                <div className="p-4">
                  <TiposEnoTab />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="agentes">
              <div className="border border-border bg-background rounded-lg overflow-hidden">
                <div className="p-4 border-b border-border">
                  <h2 className="font-medium">Agentes Etiológicos</h2>
                  <p className="text-sm text-muted-foreground">
                    Catálogo de patógenos con estadísticas de detección
                  </p>
                </div>
                <div className="p-4">
                  <AgentesTab />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
