/**
 * SearchableCombobox Component
 * A clean implementation of a searchable combobox with infinite scroll
 * Built with controlled state and proper separation of concerns
 */

import * as React from "react";
import { Check, ChevronsUpDown, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export interface ComboboxOption {
  value: string;
  label: string;
}

interface SearchableComboboxProps {
  // Required props
  options: ComboboxOption[];
  value?: string;
  onValueChange: (value: string) => void;
  onSearch: (search: string) => void;
  onLoadMore?: () => void;

  // State props
  hasMore?: boolean;
  isLoading?: boolean;

  // UI props
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
  disabled?: boolean;
}

export function SearchableCombobox({
  options,
  value,
  onValueChange,
  onSearch,
  onLoadMore,
  hasMore = false,
  isLoading = false,
  placeholder = "Seleccionar...",
  searchPlaceholder = "Buscar...",
  emptyMessage = "No se encontraron resultados.",
  className,
  disabled = false,
}: SearchableComboboxProps) {
  // Simple controlled state
  const [open, setOpen] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");

  // Refs for infinite scroll
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const loadMoreRef = React.useRef<HTMLDivElement>(null);

  // Debounced search effect
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Call search when debounced term changes
  React.useEffect(() => {
    if (open) {
      onSearch(debouncedSearchTerm);
    }
  }, [debouncedSearchTerm, onSearch, open]);

  // Reset search when closing (only if not currently debouncing)
  React.useEffect(() => {
    if (!open && searchTerm !== debouncedSearchTerm) {
      setSearchTerm("");
    }
  }, [open, searchTerm, debouncedSearchTerm]);

  // Focus input when popover opens
  React.useEffect(() => {
    if (open) {
      setTimeout(() => {
        const input = document.querySelector('[cmdk-input]') as HTMLInputElement;
        if (input) {
          input.focus();
        }
      }, 100);
    }
  }, [open]);

  // Infinite scroll observer
  React.useEffect(() => {
    if (!open || !hasMore || isLoading || !onLoadMore || !loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          onLoadMore();
        }
      },
      {
        root: scrollRef.current,
        rootMargin: "50px",
        threshold: 0.1,
      }
    );

    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [open, hasMore, isLoading, onLoadMore]);

  const selectedLabel = options.find(opt => opt.value === value)?.label;

  const handleSelect = (optionValue: string) => {
    onValueChange(optionValue);
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            "w-full justify-between",
            !value && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          {selectedLabel || placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        className="w-full p-0"
        align="start"
        onOpenAutoFocus={(e) => e.preventDefault()}
        sideOffset={4}
      >
        <Command shouldFilter={false} loop={false}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={searchTerm}
            onValueChange={setSearchTerm}
          />

          {options.length === 0 && !isLoading && (
            <CommandEmpty>{emptyMessage}</CommandEmpty>
          )}

          <CommandGroup
            ref={scrollRef}
            className="max-h-[300px] overflow-auto"
          >
            {/* Render options */}
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={option.value}
                onSelect={() => handleSelect(option.value)}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    value === option.value ? "opacity-100" : "opacity-0"
                  )}
                />
                {option.label}
              </CommandItem>
            ))}

            {/* Loading state */}
            {isLoading && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">
                  {options.length === 0 ? "Buscando..." : "Cargando más..."}
                </span>
              </div>
            )}

            {/* Load more trigger (invisible) */}
            {hasMore && !isLoading && options.length > 0 && (
              <div
                ref={loadMoreRef}
                className="h-1"
                aria-hidden="true"
              />
            )}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

// Custom hook for debouncing
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}