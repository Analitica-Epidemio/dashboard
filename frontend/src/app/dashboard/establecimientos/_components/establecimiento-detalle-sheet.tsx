"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useEstablecimientoDetalle, type PersonaRelacionada } from "@/lib/api/mapa";
import { Calendar, Building2, Users, Activity, Link2 } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface EstablecimientoDetalleSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idEstablecimiento: number | null;
}

export function EstablecimientoDetalleSheet({
  open,
  onOpenChange,
  idEstablecimiento,
}: EstablecimientoDetalleSheetProps) {
  const { data, isLoading } = useEstablecimientoDetalle(idEstablecimiento, open);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-3xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-red-600" />
            {isLoading ? (
              <Skeleton className="h-6 w-64" />
            ) : (
              data?.nombre || "Establecimiento"
            )}
          </SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <LoadingSkeleton />
        ) : data ? (
          <div className="mt-6 space-y-6">
            {/* Resumen del establecimiento */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={<Users className="h-4 w-4" />}
                label="Total Personas"
                value={data.total_personas}
                variant="default"
              />
              {data.codigo_refes && (
                <StatCard
                  icon={<Building2 className="h-4 w-4" />}
                  label="Código REFES"
                  value={data.codigo_refes}
                  variant="secondary"
                />
              )}
              {data.codigo_snvs && (
                <StatCard
                  icon={<Building2 className="h-4 w-4" />}
                  label="Código SNVS"
                  value={data.codigo_snvs}
                  variant="secondary"
                />
              )}
              {data.localidad_nombre && (
                <StatCard
                  icon={<Building2 className="h-4 w-4" />}
                  label="Localidad"
                  value={data.localidad_nombre}
                  variant="secondary"
                />
              )}
            </div>

            {/* Relaciones por tipo */}
            {Object.keys(data.relaciones_por_tipo).length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Link2 className="h-4 w-4" />
                  Relaciones por Tipo
                </h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(data.relaciones_por_tipo).map(([tipo, count]) => (
                    <Badge key={tipo} variant="outline" className="px-3 py-1">
                      {getTipoRelacionLabel(tipo)}: <span className="font-bold ml-1">{count}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Eventos por tipo */}
            {Object.keys(data.eventos_por_tipo).length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Eventos por Tipo
                </h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(data.eventos_por_tipo).map(([tipo, count]) => (
                    <Badge key={tipo} variant="outline" className="px-3 py-1">
                      {tipo}: <span className="font-bold ml-1">{count}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Lista de personas relacionadas */}
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4" />
                Personas Relacionadas ({data.personas.length})
              </h3>

              {data.personas.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No hay personas relacionadas con este establecimiento
                </div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {data.personas.map((persona, idx) => (
                    <PersonaCard key={`${persona.codigo_ciudadano}-${persona.id_evento}-${idx}`} persona={persona} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No se encontraron datos del establecimiento
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function StatCard({
  icon,
  label,
  value,
  variant = "default",
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  variant?: "default" | "secondary";
}) {
  return (
    <div
      className={`p-4 rounded-lg border ${
        variant === "default"
          ? "bg-red-50 border-red-200"
          : "bg-gray-50 border-gray-200"
      }`}
    >
      <div className="flex items-center gap-2 text-gray-600 mb-1">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div
        className="text-lg font-bold text-gray-900 truncate"
        title={String(value)}
      >
        {value}
      </div>
    </div>
  );
}

function PersonaCard({ persona }: { persona: PersonaRelacionada }) {
  return (
    <div className="p-4 rounded-lg border border-gray-200 hover:border-red-300 hover:bg-red-50/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          {/* Tipo de relación y evento */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="default" className="bg-red-600 hover:bg-red-700">
              {getTipoRelacionLabel(persona.tipo_relacion)}
            </Badge>
            {persona.tipo_evento_nombre && (
              <Badge variant="secondary">{persona.tipo_evento_nombre}</Badge>
            )}
            {persona.grupo_evento_nombre && (
              <Badge variant="outline">{persona.grupo_evento_nombre}</Badge>
            )}
            {persona.clasificacion_manual && (
              <Badge variant="outline">{persona.clasificacion_manual}</Badge>
            )}
            {persona.estado && (
              <Badge
                variant={persona.estado === "Confirmado" ? "default" : "secondary"}
              >
                {persona.estado}
              </Badge>
            )}
          </div>

          {/* Datos del ciudadano */}
          <div className="space-y-2">
            {persona.nombre_completo && (
              <div className="text-sm">
                <span className="font-semibold text-gray-900">
                  {persona.nombre_completo}
                </span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              {persona.dni && (
                <div className="text-gray-600">
                  <span className="font-medium">DNI:</span>{" "}
                  <span className="text-gray-900">{persona.dni}</span>
                </div>
              )}
              <div className="text-gray-600">
                <span className="font-medium">Código:</span>{" "}
                <span className="text-gray-900">{persona.codigo_ciudadano}</span>
              </div>
              {persona.edad != null && (
                <div className="text-gray-600">
                  <span className="font-medium">Edad:</span>{" "}
                  <span className="text-gray-900">{persona.edad} años</span>
                </div>
              )}
              {persona.sexo && (
                <div className="text-gray-600">
                  <span className="font-medium">Sexo:</span>{" "}
                  <span className="text-gray-900">{persona.sexo}</span>
                </div>
              )}
              {persona.fecha_evento && (
                <div className="text-gray-600 flex items-center gap-1 col-span-2">
                  <Calendar className="h-3 w-3" />
                  <span className="font-medium">Fecha evento:</span>{" "}
                  <span>
                    {format(new Date(persona.fecha_evento), "dd MMM yyyy", {
                      locale: es,
                    })}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ID del evento */}
        <div className="text-right">
          <div className="text-xs text-gray-500">ID Evento</div>
          <div className="text-sm font-mono text-gray-700">
            {persona.id_evento}
          </div>
        </div>
      </div>
    </div>
  );
}

function getTipoRelacionLabel(tipo: string): string {
  const labels: Record<string, string> = {
    consulta: "Consulta",
    notificacion: "Notificación",
    carga: "Carga",
    muestra: "Muestra",
    diagnostico: "Diagnóstico",
    tratamiento: "Tratamiento",
  };
  return labels[tipo] || tipo;
}

function LoadingSkeleton() {
  return (
    <div className="mt-6 space-y-6">
      {/* Stats skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>

      {/* Relaciones por tipo skeleton */}
      <div>
        <Skeleton className="h-5 w-32 mb-3" />
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-24" />
          ))}
        </div>
      </div>

      {/* Eventos por tipo skeleton */}
      <div>
        <Skeleton className="h-5 w-32 mb-3" />
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-24" />
          ))}
        </div>
      </div>

      {/* Lista de personas skeleton */}
      <div>
        <Skeleton className="h-5 w-40 mb-3" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    </div>
  );
}
