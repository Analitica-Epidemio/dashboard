"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  Hash,
  User,
  Clock,
  Shield,
  FileText,
  Info,
  ArrowRight,
  Zap,
  Eye,
  History,
} from "lucide-react";
import { type EventStrategy, extractSuccessData } from "@/lib/api/strategies";

type Strategy = EventStrategy;

interface StrategyPreviewProps {
  strategy: Strategy;
  onClose: () => void;
}

export function StrategyPreview({ strategy, onClose }: StrategyPreviewProps) {
  const getFilterDescription = (filter: {
    filter_type: string;
    field_name?: string | null;
    value?: string | null;
    values?: string[] | null;
    logical_operator?: string | null;
  }) => {
    switch (filter.filter_type) {
      case "campo_igual":
        return (
          <span>
            El campo{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>{" "}
            es igual a <strong>&quot;{filter.value}&quot;</strong>
          </span>
        );
      case "campo_en_lista":
        return (
          <span>
            El campo{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>{" "}
            contiene uno de estos valores:{" "}
            <strong>
              {filter.values?.map((v: string) => `"${v}"`).join(", ")}
            </strong>
          </span>
        );
      case "campo_contiene":
        return (
          <span>
            El campo{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>{" "}
            contiene el texto <strong>&quot;{filter.value}&quot;</strong>
          </span>
        );
      case "campo_existe":
        return (
          <span>
            El campo{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>{" "}
            <strong>tiene un valor</strong> (no está vacío)
          </span>
        );
      case "campo_no_nulo":
        return (
          <span>
            El campo{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>{" "}
            <strong>no está vacío</strong>
          </span>
        );
      case "detector_tipo_sujeto":
        return (
          <span>
            Se detecta que el sujeto es de tipo{" "}
            <strong>
              {filter.value === "animal"
                ? "animal"
                : filter.value === "humano"
                ? "humano"
                : "indeterminado"}
            </strong>{" "}
            analizando{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>
          </span>
        );
      default:
        return (
          <span>
            {filter.filter_type}:{" "}
            <code className="bg-muted px-2 py-0.5 rounded text-xs font-medium">
              {filter.field_name}
            </code>
          </span>
        );
    }
  };

  const getClassificationLabel = (classification: string) => {
    const labels: Record<string, string> = {
      confirmados: "Caso Confirmado",
      sospechosos: "Caso Sospechoso",
      probables: "Caso Probable",
      descartados: "Caso Descartado",
      negativos: "Caso Negativo",
      requiere_revision: "Requiere Revisión Manual",
      en_estudio: "En Estudio",
    };
    return labels[classification] || classification;
  };

  const getClassificationBadgeVariant = (classification: string) => {
    const variants: Record<
      string,
      "default" | "secondary" | "destructive" | "outline"
    > = {
      confirmados: "default",
      sospechosos: "secondary",
      probables: "secondary",
      requiere_revision: "destructive",
      descartados: "outline",
      negativos: "outline",
    };
    return variants[classification] || "outline";
  };

  const hasConfidenceFilters = (
    filters: Array<{
      filter_type: string;
      confidence_applies?: boolean;
    }>
  ) => {
    return filters.some(
      (f) =>
        f.filter_type === "detector_tipo_sujeto" ||
        f.filter_type === "regex_extraccion"
    );
  };

  return (
    <div className="space-y-6">
      {/* Strategy Header Info - Acts as Sheet Header */}
      <div className="space-y-4 pb-4 border-b">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">{strategy.name}</h2>
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Hash className="h-4 w-4" />
                <span>ID: {strategy.id}</span>
              </div>
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                <span>
                  {strategy.tipo_eno_name || `Evento ${strategy.tipo_eno_id}`}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <User className="h-4 w-4" />
                <span>{strategy.created_by || "Sistema"}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>
                  {strategy.created_at
                    ? new Date(strategy.created_at).toLocaleDateString("es-ES")
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>
          <Badge
            variant={strategy.active ? "default" : "secondary"}
            className="text-sm px-3 py-1"
          >
            {strategy.active ? "Activa" : "Inactiva"}
          </Badge>
        </div>

        {/* Description if available */}
        {strategy.description && (
          <p className="text-sm text-muted-foreground">
            {strategy.description}
          </p>
        )}

        <div className="flex items-center gap-4 text-sm">
          {strategy.usa_provincia_carga && (
            <div className="flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span>Filtro por provincia activo</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <FileText className="h-4 w-4 text-green-600 dark:text-green-400" />
            <span>
              {strategy.classification_rules?.length || 0} reglas configuradas
            </span>
          </div>
          {strategy.updated_at && (
            <div className="flex items-center gap-1.5">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                Última modificación:{" "}
                {new Date(strategy.updated_at).toLocaleDateString("es-ES")}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* How it works explanation */}
      <Alert className="border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertDescription className="text-sm">
          <strong>¿Cómo funciona?</strong> Las reglas se evalúan en orden de
          prioridad (1 primero). Cuando un evento cumple todas las condiciones
          de una regla, se clasifica automáticamente con esa categoría. Si
          ninguna regla coincide, el evento queda sin clasificar.
        </AlertDescription>
      </Alert>

      {/* Classification Rules Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Reglas de Clasificación</h3>

        <div className="space-y-4">
          {strategy.classification_rules?.map((rule) => (
            <div
              key={rule.id}
              className={`border rounded-lg ${
                !rule.is_active ? "opacity-60" : ""
              }`}
            >
              {/* Rule Header */}
              <div className="p-4 bg-muted/30">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold text-muted-foreground">
                        {rule.priority}
                      </span>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          Si se cumplen las condiciones, clasificar como:
                        </span>
                        <Badge
                          variant={getClassificationBadgeVariant(
                            rule.classification
                          )}
                          className="text-sm"
                        >
                          {getClassificationLabel(rule.classification)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {rule.auto_approve ? (
                          <div className="flex items-center gap-1">
                            <Zap className="h-3 w-3" />
                            <span>Clasificación automática</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            <span>Requiere revisión manual</span>
                          </div>
                        )}
                        {!rule.is_active && (
                          <Badge variant="secondary" className="text-xs">
                            Regla desactivada
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Confidence explanation if applicable */}
                {hasConfidenceFilters(rule.filters) &&
                  rule.required_confidence && (
                    <Alert className="mb-3 border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/20">
                      <Info className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                      <AlertDescription className="text-xs">
                        <strong>
                          Nivel de confianza requerido:{" "}
                          {(rule.required_confidence * 100).toFixed(0)}%
                        </strong>
                        <br />
                        Esta regla usa detección inteligente. Solo se aplicará
                        si el sistema tiene al menos{" "}
                        {(rule.required_confidence * 100).toFixed(0)}% de
                        certeza en la detección.
                      </AlertDescription>
                    </Alert>
                  )}
              </div>

              {/* Rule Conditions */}
              <div className="p-4">
                <div className="space-y-3">
                  <div className="text-sm font-medium text-muted-foreground">
                    Condiciones que deben cumplirse:
                  </div>
                  <div className="space-y-2 pl-4">
                    {rule.filters.map((filter, filterIndex) => (
                      <div key={filter.id} className="space-y-1">
                        <div className="flex items-start gap-2">
                          <div className="mt-0.5">
                            <div className="w-2 h-2 rounded-full bg-muted-foreground/50" />
                          </div>
                          <div className="flex-1 text-sm">
                            {getFilterDescription(filter)}
                          </div>
                        </div>
                        {filterIndex < rule.filters.length - 1 && (
                          <div className="ml-10 text-xs text-muted-foreground font-medium">
                            {filter.logical_operator === "AND"
                              ? "+ también debe cumplirse:"
                              : "o alternativamente:"}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      <div className="flex justify-end pt-4">
        <Button onClick={onClose}>Cerrar</Button>
      </div>
    </div>
  );
}
