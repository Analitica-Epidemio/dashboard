"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useDomicilioDetalle, type CasoDetalle } from "@/features/mapa/api";
import { Calendar, MapPin, Users, Activity } from "lucide-react";
import { format } from "date-fns";
import { es } from "date-fns/locale";

interface DomicilioDetalleSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idDomicilio: number | null;
}

export function DomicilioDetalleSheet({
  open,
  onOpenChange,
  idDomicilio,
}: DomicilioDetalleSheetProps) {
  const { data, isLoading } = useDomicilioDetalle(idDomicilio, { enabled: open });

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-3xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-blue-600" />
            {isLoading ? (
              <Skeleton className="h-6 w-64" />
            ) : (
              data?.data?.direccion || "Domicilio"
            )}
          </SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <LoadingSkeleton />
        ) : data?.data ? (
          <div className="mt-6 space-y-6">
            {/* Resumen del domicilio */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={<Users className="h-4 w-4" />}
                label="Total Casos"
                value={data.data.total_casos}
                variant="default"
              />
              <StatCard
                icon={<MapPin className="h-4 w-4" />}
                label="Localidad"
                value={data.data.localidad_nombre}
                variant="secondary"
              />
              <StatCard
                icon={<MapPin className="h-4 w-4" />}
                label="Provincia"
                value={data.data.provincia_nombre}
                variant="secondary"
              />
              <StatCard
                icon={<Activity className="h-4 w-4" />}
                label="Coordenadas"
                value={`${data.data.latitud.toFixed(4)}, ${data.data.longitud.toFixed(
                  4
                )}`}
                variant="secondary"
              />
            </div>

            {/* Casos por tipo */}
            {data.data.casos_por_tipo && Object.keys(data.data.casos_por_tipo).length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Casos por Tipo
                </h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(data.data.casos_por_tipo).map(([tipo, count]) => (
                    <Badge key={tipo} variant="outline" className="px-3 py-1">
                      {tipo}: <span className="font-bold ml-1">{count as number}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Lista de casos */}
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4" />
                Lista de Casos ({data.data.casos?.length || 0})
              </h3>

              {!data.data.casos || data.data.casos.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No hay casos registrados en este domicilio
                </div>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {data.data.casos.map((caso) => (
                    <CasoCard key={caso.id_evento} caso={caso} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No se encontraron datos del domicilio
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
          ? "bg-blue-50 border-blue-200"
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

function CasoCard({ caso }: { caso: CasoDetalle }) {
  return (
    <div className="p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          {/* Tipo de evento y clasificación */}
          <div className="flex items-center gap-2 flex-wrap">
            {caso.tipo_evento_nombre && (
              <Badge variant="default">{caso.tipo_evento_nombre}</Badge>
            )}
            {caso.grupo_evento_nombre && (
              <Badge variant="secondary">{caso.grupo_evento_nombre}</Badge>
            )}
            {caso.clasificacion_manual && (
              <Badge variant="outline">{caso.clasificacion_manual}</Badge>
            )}
            {caso.estado && (
              <Badge
                variant={caso.estado === "Confirmado" ? "default" : "secondary"}
              >
                {caso.estado}
              </Badge>
            )}
          </div>

          {/* Datos del ciudadano */}
          <div className="space-y-2">
            {caso.nombre_completo && (
              <div className="text-sm">
                <span className="font-semibold text-gray-900">
                  {caso.nombre_completo}
                </span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              {caso.dni && (
                <div className="text-gray-600">
                  <span className="font-medium">DNI:</span>{" "}
                  <span className="text-gray-900">{caso.dni}</span>
                </div>
              )}
              <div className="text-gray-600">
                <span className="font-medium">Código:</span>{" "}
                <span className="text-gray-900">{caso.codigo_ciudadano}</span>
              </div>
              {caso.edad != null && (
                <div className="text-gray-600">
                  <span className="font-medium">Edad:</span>{" "}
                  <span className="text-gray-900">{caso.edad} años</span>
                </div>
              )}
              {caso.sexo && (
                <div className="text-gray-600">
                  <span className="font-medium">Sexo:</span>{" "}
                  <span className="text-gray-900">{caso.sexo}</span>
                </div>
              )}
              {caso.fecha_evento && (
                <div className="text-gray-600 flex items-center gap-1 col-span-2">
                  <Calendar className="h-3 w-3" />
                  <span className="font-medium">Fecha evento:</span>{" "}
                  <span>
                    {format(new Date(caso.fecha_evento), "dd MMM yyyy", {
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
            {caso.id_evento}
          </div>
        </div>
      </div>
    </div>
  );
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

      {/* Casos por tipo skeleton */}
      <div>
        <Skeleton className="h-5 w-32 mb-3" />
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-24" />
          ))}
        </div>
      </div>

      {/* Lista de casos skeleton */}
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
