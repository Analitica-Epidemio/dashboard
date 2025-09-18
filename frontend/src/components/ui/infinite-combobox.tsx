/**
 * InfiniteCombobox Component
 * A searchable single-select dropdown with infinite scroll support
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
  onSearch: (search: string) => void;  // Required - backend handles filtering
  onLoadMore: () => void;  // Required - for infinite scroll
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
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const [isSearching, setIsSearching] = React.useState(false);
  const [preventAutoClose, setPreventAutoClose] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const loadMoreRef = React.useRef<HTMLDivElement>(null);
  const searchTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Handle search changes with proper debouncing
  React.useEffect(() => {
    console.log('[InfiniteCombobox] Search effect triggered - open:', open, 'search:', search, 'isSearching:', isSearching);

    if (open) {
      // Clear any existing timeout
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      setIsSearching(true);
      setPreventAutoClose(true);

      searchTimeoutRef.current = setTimeout(() => {
        console.log('[InfiniteCombobox] Calling onSearch with:', search);
        onSearch(search);
        // Only clear isSearching, let the options effect handle preventAutoClose
        setIsSearching(false);
      }, 300); // Debounce search

      return () => {
        if (searchTimeoutRef.current) {
          clearTimeout(searchTimeoutRef.current);
        }
      };
    } else {
      console.log('[InfiniteCombobox] Popover is closed, not searching');
    }
  }, [search, onSearch, open]);

  // Intersection observer for infinite scroll
  React.useEffect(() => {
    if (!open || !hasMore || isLoading) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          onLoadMore();
        }
      },
      {
        root: scrollRef.current,
        rootMargin: "50px",
        threshold: 0.1,
      }
    );

    const loadMoreElement = loadMoreRef.current;
    if (loadMoreElement) {
      observer.observe(loadMoreElement);
    }

    return () => {
      if (loadMoreElement) {
        observer.unobserve(loadMoreElement);
      }
    };
  }, [open, hasMore, isLoading, onLoadMore]);

  const selectedLabel = options.find(opt => opt.value === value)?.label;

  // No local filtering - backend handles all filtering
  React.useEffect(() => {
    console.log('[InfiniteCombobox] Options received from backend:', options.length, 'items', 'open:', open, 'isSearching:', isSearching);
    // When new options arrive, keep the popover protection active for a bit longer
    if (options.length > 0 && open) {
      setPreventAutoClose(true);
      // Clear the protection after options have had time to render
      const timer = setTimeout(() => {
        console.log('[InfiniteCombobox] Clearing preventAutoClose after options rendered');
        setPreventAutoClose(false);
      }, 200);

      return () => clearTimeout(timer);
    }
  }, [options, open]);

  // Track open/close state changes
  React.useEffect(() => {
    console.log('[InfiniteCombobox] Open state changed:', open, 'isSearching:', isSearching);
  }, [open]);

  // Reset search when popover closes (but don't reset during search)
  React.useEffect(() => {
    if (!open && !isSearching) {
      console.log('[InfiniteCombobox] Resetting search because popover closed');
      setSearch("");
    }
  }, [open, isSearching]);

  return (
    <Popover
      open={open}
      onOpenChange={(newOpen) => {
        // Prevent closing during search operations or when explicitly prevented
        if (!newOpen && (isSearching || preventAutoClose)) {
          console.log('[InfiniteCombobox] Preventing close during search - isSearching:', isSearching, 'preventAutoClose:', preventAutoClose);
          return;
        }
        console.log('[InfiniteCombobox] Popover state change:', newOpen, 'isSearching:', isSearching, 'preventAutoClose:', preventAutoClose);
        setOpen(newOpen);
      }}
    >
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
      <PopoverContent className="w-full p-0" align="start" onOpenAutoFocus={(e) => e.preventDefault()}>
        <Command shouldFilter={false} loop={false}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={search}
            onValueChange={(newValue) => {
              console.log('[InfiniteCombobox] CommandInput value changing from:', search, 'to:', newValue);
              setSearch(newValue);
            }}
            autoFocus
          />
          {options.length === 0 && !isLoading && !isSearching && (
            <CommandEmpty>{emptyMessage}</CommandEmpty>
          )}
          <CommandGroup
            ref={scrollRef}
            className="max-h-[300px] overflow-auto"
            onScroll={(e) => {
              // Trigger load more when scrolling near bottom
              const target = e.currentTarget;
              if (
                hasMore &&
                !isLoading &&
                target.scrollHeight - target.scrollTop <= target.clientHeight + 100
              ) {
                onLoadMore();
              }
            }}
          >
            {/* Show frequent items when no search */}
            {!search && options.length > 5 && (
              <>
                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                  Elementos frecuentes
                </div>
                {options.slice(0, 5).map((option) => (
                  <CommandItem
                    key={`suggested-${option.value}`}
                    value={`suggested-${option.value}`}
                    onSelect={(currentValue) => {
                      console.log('[InfiniteCombobox] Suggested item selected:', currentValue, option.value);
                      onValueChange(option.value);
                      setOpen(false);
                      setSearch("");
                    }}
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
                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground border-t mt-1">
                  Todos los elementos
                </div>
              </>
            )}

            {/* All options from backend (already filtered) */}
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={String(option.value)}
                onSelect={(currentValue) => {
                  console.log('[InfiniteCombobox] Option selected:', currentValue, option.value);
                  onValueChange(option.value);
                  setOpen(false);
                  setSearch("");
                }}
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

            {/* Show loading state while searching */}
            {isSearching && options.length === 0 && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span className="text-sm text-muted-foreground">Buscando...</span>
              </div>
            )}

            {/* Load more trigger */}
            {(hasMore || isLoading) && options.length > 0 && (
              <div
                ref={loadMoreRef}
                className="flex items-center justify-center p-2 border-t"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    <span className="text-sm text-muted-foreground">Cargando más...</span>
                  </>
                ) : (
                  hasMore && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onLoadMore}
                      className="w-full"
                    >
                      Cargar más resultados
                    </Button>
                  )
                )}
              </div>
            )}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}