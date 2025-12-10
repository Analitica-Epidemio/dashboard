"use client";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const PROVINCIAS = [
    { id: "all", label: "Todas las provincias" },
    { id: "buenos_aires", label: "Buenos Aires" },
    { id: "caba", label: "CABA" },
    { id: "catamarca", label: "Catamarca" },
    { id: "chaco", label: "Chaco" },
    { id: "chubut", label: "Chubut" },
    { id: "cordoba", label: "Córdoba" },
    { id: "corrientes", label: "Corrientes" },
    { id: "entre_rios", label: "Entre Ríos" },
    { id: "formosa", label: "Formosa" },
    { id: "jujuy", label: "Jujuy" },
    { id: "la_pampa", label: "La Pampa" },
    { id: "la_rioja", label: "La Rioja" },
    { id: "mendoza", label: "Mendoza" },
    { id: "misiones", label: "Misiones" },
    { id: "neuquen", label: "Neuquén" },
    { id: "rio_negro", label: "Río Negro" },
    { id: "salta", label: "Salta" },
    { id: "san_juan", label: "San Juan" },
    { id: "san_luis", label: "San Luis" },
    { id: "santa_cruz", label: "Santa Cruz" },
    { id: "santa_fe", label: "Santa Fe" },
    { id: "santiago_del_estero", label: "Santiago del Estero" },
    { id: "tierra_del_fuego", label: "Tierra del Fuego" },
    { id: "tucuman", label: "Tucumán" },
];

interface ProvinciaSelectProps {
    value: string;
    onChange: (value: string) => void;
    className?: string;
}

export function ProvinciaSelect({ value, onChange, className }: ProvinciaSelectProps) {
    return (
        <Select value={value} onValueChange={onChange}>
            <SelectTrigger className={cn("w-[180px]", className)}>
                <SelectValue placeholder="Provincia" />
            </SelectTrigger>
            <SelectContent>
                {PROVINCIAS.map((prov) => (
                    <SelectItem key={prov.id} value={prov.id}>
                        {prov.label}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}

export default ProvinciaSelect;
