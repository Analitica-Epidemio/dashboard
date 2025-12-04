"use client";

/**
 * Design System Components for Block Config Panel
 * Reusable UI components with modern design patterns
 */

import { useState, useMemo, useCallback } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Check,
  X,
  AlertTriangle,
  Sparkles,
  Search,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ════════════════════════════════════════════════════════════════════════════
// SECTION CARD - Groups related controls
// ════════════════════════════════════════════════════════════════════════════

interface SectionCardProps {
  title: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}

export function SectionCard({ title, icon: Icon, children, className }: SectionCardProps) {
  return (
    <div className={cn("rounded-xl border bg-card overflow-hidden", className)}>
      {title && (
        <div className="flex items-center gap-2 px-4 py-3 bg-muted/30 border-b">
          {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
          <span className="text-sm font-medium text-muted-foreground">{title}</span>
        </div>
      )}
      <div className="p-4 space-y-4">
        {children}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// CONTEXT BANNER - Explains what the block does
// ════════════════════════════════════════════════════════════════════════════

interface ContextBannerProps {
  children: React.ReactNode;
  variant?: "info" | "warning" | "success";
}

export function ContextBanner({ children, variant = "info" }: ContextBannerProps) {
  const styles = {
    info: "bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 text-blue-800",
    warning: "bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200 text-amber-800",
    success: "bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200 text-emerald-800",
  };
  const icons = {
    info: <Sparkles className="h-4 w-4 shrink-0" />,
    warning: <AlertTriangle className="h-4 w-4 shrink-0" />,
    success: <Check className="h-4 w-4 shrink-0" />,
  };

  return (
    <div className={cn("flex items-start gap-3 p-3 rounded-lg border", styles[variant])}>
      {icons[variant]}
      <p className="text-sm leading-relaxed">{children}</p>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MULTI-SELECT - Modern multi-select with search
// ════════════════════════════════════════════════════════════════════════════

interface MultiSelectItem {
  codigo: string;
  nombre: string;
}

interface MultiSelectProps {
  label: string;
  helpText?: string;
  items: MultiSelectItem[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  required?: boolean;
  maxHeight?: number;
}

export function MultiSelect({
  label,
  helpText,
  items,
  selected,
  onChange,
  placeholder = "Buscar...",
  required,
  maxHeight = 200,
}: MultiSelectProps) {
  const [search, setSearch] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const filtered = useMemo(() => {
    if (!search) return items;
    const lower = search.toLowerCase();
    return items.filter(
      (i) =>
        i.nombre.toLowerCase().includes(lower) ||
        i.codigo.toLowerCase().includes(lower)
    );
  }, [items, search]);

  const toggleItem = useCallback(
    (codigo: string) => {
      if (selected.includes(codigo)) {
        onChange(selected.filter((c) => c !== codigo));
      } else {
        onChange([...selected, codigo]);
      }
    },
    [selected, onChange]
  );

  const selectedItems = useMemo(
    () => items.filter((i) => selected.includes(i.codigo)),
    [items, selected]
  );

  const showRequired = required && selected.length === 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{label}</Label>
        {showRequired && (
          <Badge
            variant="outline"
            className="text-[10px] px-1.5 py-0 border-amber-300 text-amber-600 bg-amber-50"
          >
            Requerido
          </Badge>
        )}
      </div>

      {helpText && <p className="text-xs text-muted-foreground">{helpText}</p>}

      {/* Selected items */}
      {selectedItems.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selectedItems.map((item) => (
            <Badge
              key={item.codigo}
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-destructive/10 hover:text-destructive transition-colors group pl-2 pr-1 py-0.5"
              onClick={() => toggleItem(item.codigo)}
            >
              <span className="truncate max-w-[120px]">{item.nombre}</span>
              <X className="h-3 w-3 ml-1 opacity-50 group-hover:opacity-100" />
            </Badge>
          ))}
        </div>
      )}

      {/* Search and list */}
      <div className="rounded-lg border overflow-hidden bg-background shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={placeholder}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setIsExpanded(true);
            }}
            onFocus={() => setIsExpanded(true)}
            className="border-0 border-b rounded-none pl-9 focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>

        <div
          className="overflow-y-auto transition-all duration-200"
          style={{ maxHeight: isExpanded ? maxHeight : 0 }}
        >
          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground p-4 text-center">
              No se encontraron resultados
            </p>
          ) : (
            <div className="divide-y">
              {filtered.slice(0, 50).map((item) => {
                const isSelected = selected.includes(item.codigo);
                return (
                  <div
                    key={item.codigo}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors",
                      isSelected
                        ? "bg-primary/5 hover:bg-primary/10"
                        : "hover:bg-muted/50"
                    )}
                    onClick={() => toggleItem(item.codigo)}
                  >
                    <div
                      className={cn(
                        "w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all",
                        isSelected
                          ? "bg-primary border-primary"
                          : "border-muted-foreground/30"
                      )}
                    >
                      {isSelected && (
                        <Check className="h-3 w-3 text-primary-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm truncate block">{item.nombre}</span>
                    </div>
                    <code className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">
                      {item.codigo}
                    </code>
                  </div>
                );
              })}
              {filtered.length > 50 && (
                <p className="text-xs text-muted-foreground text-center py-2">
                  Mostrando 50 de {filtered.length} resultados
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// OPTION SELECTOR - Radio-style selection
// ════════════════════════════════════════════════════════════════════════════

interface OptionSelectorOption {
  value: string;
  label: string;
  description?: string;
  icon?: LucideIcon;
}

interface OptionSelectorProps {
  label: string;
  helpText?: string;
  options: OptionSelectorOption[];
  selected: string;
  onChange: (value: string) => void;
}

export function OptionSelector({
  label,
  helpText,
  options,
  selected,
  onChange,
}: OptionSelectorProps) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">{label}</Label>
      {helpText && <p className="text-xs text-muted-foreground">{helpText}</p>}

      <div className="grid gap-2">
        {options.map((opt) => {
          const Icon = opt.icon;
          const isSelected = selected === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg border-2 text-left transition-all",
                isSelected
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-transparent bg-muted/30 hover:bg-muted/50"
              )}
              onClick={() => onChange(opt.value)}
            >
              <div
                className={cn(
                  "w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                  isSelected
                    ? "border-primary bg-primary"
                    : "border-muted-foreground/40"
                )}
              >
                {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
              </div>

              {Icon && (
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    isSelected ? "text-primary" : "text-muted-foreground"
                  )}
                />
              )}

              <div className="flex-1 min-w-0">
                <span
                  className={cn(
                    "text-sm font-medium block",
                    isSelected ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  {opt.label}
                </span>
                {opt.description && (
                  <span className="text-xs text-muted-foreground block mt-0.5">
                    {opt.description}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// TOGGLE SWITCH - Switch with label and description
// ════════════════════════════════════════════════════════════════════════════

interface ToggleSwitchProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function ToggleSwitch({
  label,
  description,
  checked,
  onChange,
}: ToggleSwitchProps) {
  return (
    <label className="flex items-center justify-between gap-3 p-3 rounded-lg bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors">
      <div className="space-y-0.5">
        <span className="text-sm font-medium">{label}</span>
        {description && (
          <span className="text-xs text-muted-foreground block">{description}</span>
        )}
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </label>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// NUMBER INPUT - Styled number input
// ════════════════════════════════════════════════════════════════════════════

interface NumberInputProps {
  label: string;
  helpText?: string;
  value: string;
  onChange: (value: string) => void;
  min?: number;
  max?: number;
  className?: string;
}

export function NumberInput({
  label,
  helpText,
  value,
  onChange,
  min = 1,
  max = 50,
  className,
}: NumberInputProps) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">{label}</Label>
      {helpText && <p className="text-xs text-muted-foreground">{helpText}</p>}
      <Input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn("w-28", className)}
      />
    </div>
  );
}
