"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Calendar,
  User,
  Clock,
  FileText,
  Info,
  ChevronDown,
  CheckCircle2,
  Edit,
  AlertCircle,
} from "lucide-react";
import { type EventStrategy } from "@/lib/api/strategies";
import { cn } from "@/lib/utils";

type Strategy = EventStrategy;

interface StrategyPreviewProps {
  strategy: Strategy;
  onClose: () => void;
  onEdit?: () => void;
}

// Tipos para los filtros y reglas
interface FilterConfig {
  value?: string;
  values?: string[];
  pattern?: string;
  target_type?: string;
  min_confidence?: number;
  extraction_fields?: string[];
  normalization?: Record<string, string>;
  function_name?: string;
  [key: string]: unknown;
}

interface Filter {
  id?: number | null;
  filter_type: string;
  field_name: string;
  value?: string | null;
  values?: string[] | null;
  config?: FilterConfig | null;
  extracted_metadata_field?: string | null;
  logical_operator?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

interface Rule {
  id?: number | null;
  classification: string;
  priority: number;
  is_active: boolean;
  auto_approve: boolean;
  required_confidence?: number | null;
  filters: Filter[];
  created_at?: string | null;
  updated_at?: string | null;
}

export function StrategyPreview({ strategy, onClose, onEdit }: StrategyPreviewProps) {
  // Helper para extraer valores del config
  const getConfigValue = (filter: Filter, key: string) => {
    return filter.config?.[key];
  };

  const getValue = (filter: Filter) => {
    if (filter.config?.value) return filter.config.value as string;
    return filter.value;
  };

  const getValues = (filter: Filter) => {
    if (filter.config?.values) return filter.config.values as string[];
    return filter.values;
  };

  // Descripción del filtro
  const getFilterDescription = (filter: Filter) => {
    const filterType = filter.filter_type.toLowerCase();

    switch (filterType) {
      case "campo_igual":
        return (
          <div>
            <span className="text-muted-foreground">Campo</span>{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {filter.field_name}
            </code>{" "}
            <span className="text-muted-foreground">igual a</span>{" "}
            <strong>{getValue(filter)}</strong>
          </div>
        );

      case "campo_en_lista":
        const values = getValues(filter);
        return (
          <div className="space-y-1">
            <div>
              <span className="text-muted-foreground">Campo</span>{" "}
              <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
                {filter.field_name}
              </code>{" "}
              <span className="text-muted-foreground">es uno de:</span>
            </div>
            <div className="flex flex-wrap gap-1 mt-1">
              {values?.map((v: string, i: number) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {v}
                </Badge>
              ))}
            </div>
          </div>
        );

      case "campo_contiene":
        return (
          <div>
            <span className="text-muted-foreground">Campo</span>{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {filter.field_name}
            </code>{" "}
            <span className="text-muted-foreground">contiene</span>{" "}
            <strong>{getValue(filter)}</strong>
          </div>
        );

      case "campo_existe":
        return (
          <div>
            <span className="text-muted-foreground">Campo</span>{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {filter.field_name}
            </code>{" "}
            <span className="text-muted-foreground">existe</span>
          </div>
        );

      case "campo_no_nulo":
        return (
          <div>
            <span className="text-muted-foreground">Campo</span>{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {filter.field_name}
            </code>{" "}
            <span className="text-muted-foreground">no está vacío</span>
          </div>
        );

      case "regex_extraccion":
        return (
          <div className="space-y-1">
            <div>
              <span className="text-muted-foreground">Extrae usando regex del campo</span>{" "}
              <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
                {filter.field_name}
              </code>
            </div>
            {(() => {
              const pattern = getConfigValue(filter, "pattern");
              return pattern && typeof pattern === 'string' ? (
                <code className="block bg-muted px-2 py-1 rounded text-xs font-mono mt-1">
                  {pattern}
                </code>
              ) : null;
            })()}
            {filter.extracted_metadata_field && (
              <div className="text-xs text-muted-foreground mt-1">
                → Guarda en: <strong>{filter.extracted_metadata_field}</strong>
              </div>
            )}
          </div>
        );

      case "detector_tipo_sujeto":
        const targetType = getConfigValue(filter, "target_type") as string | undefined;
        const minConfidence = getConfigValue(filter, "min_confidence") as number | undefined;
        return (
          <div className="space-y-1">
            <div>
              <span className="text-muted-foreground">Detecta tipo de sujeto:</span>{" "}
              <strong>
                {targetType === "animal"
                  ? "Animal"
                  : targetType === "humano"
                  ? "Humano"
                  : targetType === "cualquiera"
                  ? "Cualquiera"
                  : "Indeterminado"}
              </strong>
            </div>
            {minConfidence !== undefined && minConfidence !== null && minConfidence > 0 && (
              <div className="text-xs text-muted-foreground">
                Confianza mínima: {(minConfidence * 100).toFixed(0)}%
              </div>
            )}
            {filter.extracted_metadata_field && (
              <div className="text-xs text-muted-foreground">
                → Guarda en: <strong>{filter.extracted_metadata_field}</strong>
              </div>
            )}
          </div>
        );

      case "extractor_metadata":
        const extractionFields = getConfigValue(filter, "extraction_fields") as string[] | undefined;
        const normalization = getConfigValue(filter, "normalization") as Record<string, unknown> | undefined;
        return (
          <div className="space-y-1">
            <div>
              <span className="text-muted-foreground">Extrae metadata de:</span>
            </div>
            {extractionFields && Array.isArray(extractionFields) && extractionFields.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {extractionFields.map((f: string, i: number) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {f}
                  </Badge>
                ))}
              </div>
            )}
            {normalization && typeof normalization === 'object' && Object.keys(normalization).length > 0 && (
              <div className="space-y-1 mt-1">
                <div className="text-xs text-muted-foreground font-medium">
                  Normalizaciones:
                </div>
                <div className="text-xs space-y-0.5 pl-2 border-l-2 border-muted">
                  {Object.entries(normalization).map(([k, v], i) => (
                    <div key={i}>
                      <strong>&quot;{k}&quot;</strong> → <strong>&quot;{String(v)}&quot;</strong>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {filter.extracted_metadata_field && (
              <div className="text-xs text-muted-foreground mt-1">
                → Guarda en: <strong>{filter.extracted_metadata_field}</strong>
              </div>
            )}
          </div>
        );

      case "custom_function":
        return (
          <div>
            <span className="text-muted-foreground">Función personalizada:</span>{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {(getConfigValue(filter, "function_name") as string) || filter.field_name}
            </code>
          </div>
        );

      default:
        return (
          <div>
            <Badge variant="outline" className="text-xs mr-2">
              {filter.filter_type}
            </Badge>
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              {filter.field_name}
            </code>
          </div>
        );
    }
  };

  const getClassificationLabel = (classification: string) => {
    const classificationLower = classification.toLowerCase();
    const labels: Record<string, string> = {
      confirmados: "Confirmado",
      sospechosos: "Sospechoso",
      probables: "Probable",
      descartados: "Descartado",
      negativos: "Negativo",
      requiere_revision: "Requiere Revisión",
      en_estudio: "En Estudio",
      notificados: "Notificado",
      con_resultado_mortal: "Con Resultado Mortal",
      sin_resultado_mortal: "Sin Resultado Mortal",
    };
    return labels[classificationLower] || classification;
  };

  const getClassificationColor = (classification: string) => {
    const classificationLower = classification.toLowerCase();
    const colors: Record<string, string> = {
      confirmados: "bg-red-500",
      sospechosos: "bg-orange-500",
      probables: "bg-amber-500",
      requiere_revision: "bg-purple-500",
      descartados: "bg-gray-500",
      negativos: "bg-green-500",
      en_estudio: "bg-blue-500",
      notificados: "bg-cyan-500",
      con_resultado_mortal: "bg-red-900",
      sin_resultado_mortal: "bg-green-600",
    };
    return colors[classificationLower] || "bg-gray-500";
  };

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold">{strategy.name}</h2>
            <p className="text-sm text-muted-foreground">
              {strategy.tipo_eno_name || `Evento ${strategy.tipo_eno_id}`}
            </p>
          </div>
          <Badge
            variant={strategy.active ? "default" : "secondary"}
            className="shrink-0"
          >
            {strategy.active ? "Activa" : "Inactiva"}
          </Badge>
        </div>

        {strategy.description && (
          <p className="text-sm text-muted-foreground leading-relaxed">
            {strategy.description}
          </p>
        )}

        {/* Meta info */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>
              {formatDate(strategy.valid_from)} -{" "}
              {strategy.valid_until ? formatDate(strategy.valid_until) : "∞"}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            <span>{strategy.classification_rules?.length || 0} reglas</span>
          </div>
          {strategy.created_by && (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span>{strategy.created_by}</span>
            </div>
          )}
          {strategy.updated_at && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>
                Actualizada: {formatDate(strategy.updated_at)}
              </span>
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* How it works */}
      <Alert className="border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        <AlertDescription className="text-sm">
          Las reglas se evalúan por prioridad. Cuando un evento cumple todas las
          condiciones de una regla, se clasifica automáticamente.
        </AlertDescription>
      </Alert>

      {/* Rules */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold">
          Reglas de Clasificación ({strategy.classification_rules?.length || 0})
        </h3>

        {!strategy.classification_rules || strategy.classification_rules.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            No hay reglas configuradas
          </div>
        ) : (
          <div className="space-y-2">
            {strategy.classification_rules.map((rule) => (
              <RuleCard
                key={rule.id}
                rule={rule}
                getFilterDescription={getFilterDescription}
                getClassificationLabel={getClassificationLabel}
                getClassificationColor={getClassificationColor}
              />
            ))}
          </div>
        )}
      </div>

      <Separator />

      {/* Actions */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>
          Cerrar
        </Button>
        {onEdit && (
          <Button onClick={onEdit}>
            <Edit className="mr-2 h-4 w-4" />
            Editar
          </Button>
        )}
      </div>
    </div>
  );
}

// Componente para cada regla (colapsable)
interface RuleCardProps {
  rule: Rule;
  getFilterDescription: (filter: Filter) => React.ReactNode;
  getClassificationLabel: (classification: string) => string;
  getClassificationColor: (classification: string) => string;
}

function RuleCard({
  rule,
  getFilterDescription,
  getClassificationLabel,
  getClassificationColor,
}: RuleCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div
        className={cn(
          "border rounded-lg overflow-hidden transition-all",
          !rule.is_active && "opacity-60"
        )}
      >
        <CollapsibleTrigger asChild>
          <button
            className="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-muted/50 transition-colors text-left"
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Priority number */}
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-sm font-semibold shrink-0">
                {rule.priority}
              </div>

              {/* Classification badge */}
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-sm text-muted-foreground shrink-0">Clasifica como:</span>
                <Badge
                  className={cn(
                    getClassificationColor(rule.classification),
                    "text-white"
                  )}
                >
                  {getClassificationLabel(rule.classification)}
                </Badge>
              </div>

              {/* Info badges */}
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="outline" className="text-xs">
                  {rule.filters?.length || 0} condiciones
                </Badge>
                {!rule.is_active && (
                  <Badge variant="secondary" className="text-xs">
                    Inactiva
                  </Badge>
                )}
              </div>
            </div>

            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform shrink-0",
                isOpen && "transform rotate-180"
              )}
            />
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 py-3 border-t bg-muted/30 space-y-3">
            {/* Auto approve info */}
            <div className="flex items-start gap-2 text-xs">
              {rule.auto_approve ? (
                <div className="flex items-center gap-1 text-muted-foreground">
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Clasificación automática</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 text-amber-600">
                  <AlertCircle className="h-3 w-3" />
                  <span>Requiere revisión manual</span>
                </div>
              )}
              {rule.required_confidence && rule.required_confidence > 0 && (
                <div className="text-muted-foreground">
                  · Confianza mínima: {(rule.required_confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>

            {/* Filters */}
            {rule.filters && rule.filters.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-medium text-muted-foreground">
                  Condiciones:
                </div>
                <div className="space-y-2">
                  {rule.filters.map((filter: Filter, filterIndex: number) => (
                    <div key={filter.id || filterIndex} className="space-y-1">
                      <div className="flex items-start gap-2 text-sm pl-2 border-l-2 border-muted-foreground/30">
                        <div className="flex-1">
                          {getFilterDescription(filter)}
                        </div>
                      </div>
                      {filterIndex < rule.filters.length - 1 && (
                        <div className="text-xs text-muted-foreground font-medium pl-4">
                          {filter.logical_operator === "AND" ? "Y" : "O"}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
