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

const AGENTES = [
    { id: "influenza_a", label: "Influenza A", color: "bg-blue-500" },
    { id: "influenza_b", label: "Influenza B", color: "bg-green-500" },
    { id: "sars_cov_2", label: "SARS-CoV-2", color: "bg-red-500" },
    { id: "vsr", label: "VSR", color: "bg-purple-500" },
    { id: "adenovirus", label: "Adenovirus", color: "bg-yellow-500" },
    { id: "parainfluenza", label: "Parainfluenza", color: "bg-orange-500" },
    { id: "metapneumovirus", label: "Metapneumovirus", color: "bg-teal-500" },
    { id: "rinovirus", label: "Rinovirus", color: "bg-pink-500" },
];

interface AgenteFilterProps {
    value: string[];
    onChange: (value: string[]) => void;
    className?: string;
    placeholder?: string;
}

export function AgenteFilter({
    value,
    onChange,
    className,
    placeholder = "Seleccionar agentes...",
}: AgenteFilterProps) {
    const [open, setOpen] = useState(false);

    const handleSelect = (agenteId: string) => {
        if (value.includes(agenteId)) {
            onChange(value.filter((id) => id !== agenteId));
        } else {
            onChange([...value, agenteId]);
        }
    };

    const handleRemove = (agenteId: string) => {
        onChange(value.filter((id) => id !== agenteId));
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
                        {value.length > 0 ? `${value.length} agentes` : placeholder}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[250px] p-0">
                    <Command>
                        <CommandInput placeholder="Buscar agente..." />
                        <CommandList>
                            <CommandEmpty>No se encontraron agentes.</CommandEmpty>
                            <CommandGroup>
                                {AGENTES.map((agente) => (
                                    <CommandItem
                                        key={agente.id}
                                        value={agente.id}
                                        onSelect={() => handleSelect(agente.id)}
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                value.includes(agente.id) ? "opacity-100" : "opacity-0"
                                            )}
                                        />
                                        <span className={cn("w-2 h-2 rounded-full mr-2", agente.color)} />
                                        {agente.label}
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
                        const agente = AGENTES.find((a) => a.id === id);
                        return (
                            <Badge key={id} variant="secondary" className="text-xs">
                                <span className={cn("w-2 h-2 rounded-full mr-1", agente?.color)} />
                                {agente?.label}
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

export default AgenteFilter;
