"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { Check, ChevronsUpDown, X } from "lucide-react";
import { useState } from "react";

const EVENTOS = [
    { id: "eti", label: "ETI", grupo: "respiratorias" },
    { id: "irag", label: "IRAG", grupo: "respiratorias" },
    { id: "neumonia", label: "Neumonía", grupo: "respiratorias" },
    { id: "bronquiolitis", label: "Bronquiolitis", grupo: "respiratorias" },
    { id: "covid19", label: "COVID-19", grupo: "respiratorias" },
    { id: "dengue", label: "Dengue", grupo: "vectoriales" },
    { id: "chikungunya", label: "Chikungunya", grupo: "vectoriales" },
    { id: "zika", label: "Zika", grupo: "vectoriales" },
    { id: "sarampion", label: "Sarampión", grupo: "inmunoprevenibles" },
    { id: "rubeola", label: "Rubéola", grupo: "inmunoprevenibles" },
];

interface EventoFilterProps {
    value: string[];
    onChange: (value: string[]) => void;
    grupoFilter?: string[];
    className?: string;
    placeholder?: string;
}

export function EventoFilter({
    value,
    onChange,
    grupoFilter,
    className,
    placeholder = "Seleccionar eventos...",
}: EventoFilterProps) {
    const [open, setOpen] = useState(false);

    const filteredEventos = grupoFilter?.length
        ? EVENTOS.filter((e) => grupoFilter.includes(e.grupo))
        : EVENTOS;

    const handleSelect = (eventoId: string) => {
        if (value.includes(eventoId)) {
            onChange(value.filter((id) => id !== eventoId));
        } else {
            onChange([...value, eventoId]);
        }
    };

    const handleRemove = (eventoId: string) => {
        onChange(value.filter((id) => id !== eventoId));
    };

    return (
        <div className={cn("space-y-2", className)}>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="w-full justify-between"
                    >
                        {value.length > 0 ? `${value.length} eventos` : placeholder}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[250px] p-0">
                    <Command>
                        <CommandInput placeholder="Buscar evento..." />
                        <CommandList>
                            <CommandEmpty>No se encontraron eventos.</CommandEmpty>
                            <CommandGroup>
                                {filteredEventos.map((evento) => (
                                    <CommandItem
                                        key={evento.id}
                                        value={evento.id}
                                        onSelect={() => handleSelect(evento.id)}
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                value.includes(evento.id) ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        {evento.label}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
            {value.length > 0 && (
                <div className="flex flex-wrap gap-1">
                    {value.map((id) => {
                        const evento = EVENTOS.find((e) => e.id === id);
                        return (
                            <Badge key={id} variant="secondary" className="text-xs">
                                {evento?.label}
                                <button
                                    className="ml-1 hover:text-destructive"
                                    onClick={() => handleRemove(id)}
                                >
                                    <X className="h-3 w-3" />
                                </button>
                            </Badge>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default EventoFilter;
