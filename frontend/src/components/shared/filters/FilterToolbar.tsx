"use client";

/**
 * Toolbar de búsqueda y filtros compartido
 * Diseño moderno estilo Linear/GitHub con búsqueda y acciones
 */

import React from "react";
import { Search, Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export interface FilterToolbarAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  variant?: "default" | "outline" | "ghost" | "destructive";
  hideOnMobile?: boolean;
}

export interface FilterToolbarProps {
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  onFiltersClick?: () => void;
  activeFiltersCount?: number;
  actions?: FilterToolbarAction[];
  children?: React.ReactNode;
}

export function FilterToolbar({
  searchPlaceholder = "Buscar...",
  searchValue = "",
  onSearchChange,
  onFiltersClick,
  activeFiltersCount = 0,
  actions = [],
  children,
}: FilterToolbarProps) {
  return (
    <div className="space-y-4">
      {/* Search and Actions Row */}
      <div className="flex items-center justify-between gap-4">
        {/* Search Input */}
        {onSearchChange && (
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={searchPlaceholder}
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9 pr-9 bg-background border-border"
            />
            {searchValue && (
              <button
                onClick={() => onSearchChange("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Limpiar búsqueda"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Filters Button */}
          {onFiltersClick && (
            <Button
              variant="outline"
              size="sm"
              onClick={onFiltersClick}
              className="gap-2 relative"
            >
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">Filtros</span>
              {activeFiltersCount > 0 && (
                <Badge
                  variant="default"
                  className="ml-1 h-5 min-w-5 rounded-full px-1.5 text-xs"
                >
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
          )}

          {/* Custom Actions */}
          {actions.map((action) => (
            <Button
              key={action.id}
              variant={action.variant || "outline"}
              size="sm"
              onClick={action.onClick}
              className={`gap-2 ${action.hideOnMobile ? "hidden sm:flex" : ""}`}
            >
              {action.icon}
              <span className={action.hideOnMobile ? "hidden lg:inline" : ""}>
                {action.label}
              </span>
            </Button>
          ))}
        </div>
      </div>

      {/* Children - Additional content like stats */}
      {children}
    </div>
  );
}
