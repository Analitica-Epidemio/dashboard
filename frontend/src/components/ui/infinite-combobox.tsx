/**
 * InfiniteCombobox Component
 * A searchable single-select dropdown with infinite scroll support
 *
 * APPROACH: Controlled state - we manage open/close manually
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

interface InfiniteComboboxProps {
  options: ComboboxOption[];
  value?: string;
  onValueChange: (value: string) => void;
  onSearch: (search: string) => void;
  onLoadMore: () => void;
  hasMore?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
  disabled?: boolean;
}

export function InfiniteCombobox({
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
}: InfiniteComboboxProps) {
  // Manual controlled state
  const [internalOpen, setInternalOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const searchTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = React.useRef(false);

  // Track loading state
  React.useEffect(() => {
    isLoadingRef.current = isLoading;
  }, [isLoading]);

  // Debounced search
  React.useEffect(() => {
    if (!internalOpen) return;

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      onSearch(search);
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [search, onSearch, internalOpen]);

  // Reset search when closed
  React.useEffect(() => {
    if (!internalOpen) {
      setSearch("");
    }
  }, [internalOpen]);

  const selectedLabel = options.find(opt => opt.value === value)?.label;

  // Manual close handler
  const handleClose = () => {
    // CRITICAL: Don't close if loading
    if (isLoadingRef.current) {
      return;
    }

    setInternalOpen(false);
  };

  // Manual select handler
  const handleSelect = (selectedValue: string) => {
    onValueChange(selectedValue);
    setSearch("");
    setInternalOpen(false);
  };

  return (
    <Popover
      open={internalOpen}
      onOpenChange={(open) => {
        if (open) {
          // Always allow opening
          setInternalOpen(true);
        } else {
          // Use our custom close handler
          handleClose();
        }
      }}
      modal={true}
    >
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={internalOpen}
          className={cn(
            "w-full justify-between",
            !value && "text-muted-foreground",
            className
          )}
          disabled={disabled}
          onClick={() => setInternalOpen(true)}
        >
          {selectedLabel || placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-full p-0 z-[100]"
        align="start"
        onInteractOutside={(e) => {
          // CRITICAL: Prevent closing if loading
          if (isLoadingRef.current) {
            e.preventDefault();
            return;
          }
        }}
        onEscapeKeyDown={(e) => {
          // CRITICAL: Prevent closing if loading
          if (isLoadingRef.current) {
            e.preventDefault();
            return;
          }
        }}
      >
        <Command shouldFilter={false} loop={false}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={search}
            onValueChange={setSearch}
          />
          {options.length === 0 && !isLoading && (
            <CommandEmpty>{emptyMessage}</CommandEmpty>
          )}
          <CommandGroup
            ref={scrollRef}
            className="max-h-[300px] overflow-auto"
          >
            {/* Show loading state */}
            {isLoading && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">
                  {options.length === 0 ? 'Buscando...' : 'Cargando más...'}
                </span>
              </div>
            )}

            {/* Show options */}
            {!isLoading && options.map((option) => (
              <CommandItem
                key={option.value}
                value={String(option.value)}
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

            {/* Load more button */}
            {hasMore && !isLoading && options.length > 0 && (
              <div className="flex items-center justify-center p-2 border-t">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onLoadMore();
                  }}
                  className="w-full"
                >
                  Cargar más resultados
                </Button>
              </div>
            )}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
