"use client";

/**
 * Panel de filtros avanzados compartido y reutilizable
 * Diseño moderno estilo Linear/Vercel con secciones colapsables
 */

import React from "react";
import { Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";

export interface FilterSection {
  id: string;
  title: string;
  icon?: React.ReactNode;
  description?: string;
  defaultOpen?: boolean;
  content: React.ReactNode;
}

export interface AdvancedFilterPanelProps {
  sections: FilterSection[];
  activeFiltersCount?: number;
  onClearAll?: () => void;
  className?: string;
}

export function AdvancedFilterPanel({
  sections,
  activeFiltersCount = 0,
  onClearAll,
  className = "",
}: AdvancedFilterPanelProps) {
  const [openSections, setOpenSections] = React.useState<Set<string>>(
    new Set(sections.filter((s) => s.defaultOpen).map((s) => s.id))
  );

  const toggleSection = (sectionId: string) => {
    setOpenSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header con contador de filtros activos */}
      {activeFiltersCount > 0 && onClearAll && (
        <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-900">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
              {activeFiltersCount} {activeFiltersCount === 1 ? "filtro activo" : "filtros activos"}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="h-7 text-xs gap-1 text-blue-700 hover:text-blue-900 hover:bg-blue-100 dark:text-blue-300 dark:hover:text-blue-100 dark:hover:bg-blue-900"
          >
            <X className="h-3 w-3" />
            Limpiar filtros
          </Button>
        </div>
      )}

      {/* Secciones colapsables */}
      {sections.map((section, index) => (
        <React.Fragment key={section.id}>
          <Collapsible
            open={openSections.has(section.id)}
            onOpenChange={() => toggleSection(section.id)}
          >
            <CollapsibleTrigger className="flex w-full items-center justify-between group">
              <div className="flex items-center gap-2">
                {section.icon && (
                  <div className="text-muted-foreground group-hover:text-foreground transition-colors">
                    {section.icon}
                  </div>
                )}
                <h4 className="text-sm font-semibold group-hover:text-foreground transition-colors">
                  {section.title}
                </h4>
              </div>
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${
                  openSections.has(section.id) ? "rotate-180" : ""
                }`}
              />
            </CollapsibleTrigger>

            {section.description && (
              <p className="text-xs text-muted-foreground mt-1 mb-3">
                {section.description}
              </p>
            )}

            <CollapsibleContent className="mt-4">
              {section.content}
            </CollapsibleContent>
          </Collapsible>

          {index < sections.length - 1 && <Separator />}
        </React.Fragment>
      ))}
    </div>
  );
}
