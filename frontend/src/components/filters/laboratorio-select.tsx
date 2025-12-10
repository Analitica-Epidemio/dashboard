"use client";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const LABORATORIOS = [
    { id: "all", label: "Todos los laboratorios" },
    { id: "anlis", label: "ANLIS Malbrán" },
    { id: "hospital_garrahan", label: "Hospital Garrahan" },
    { id: "hospital_gutierrez", label: "Hospital Gutiérrez" },
    { id: "hospital_muñiz", label: "Hospital Muñiz" },
    { id: "lab_central_cba", label: "Lab. Central Córdoba" },
    { id: "lab_central_sf", label: "Lab. Central Santa Fe" },
    { id: "lab_central_mza", label: "Lab. Central Mendoza" },
];

interface LaboratorioSelectProps {
    value: string;
    onChange: (value: string) => void;
    className?: string;
}

export function LaboratorioSelect({ value, onChange, className }: LaboratorioSelectProps) {
    return (
        <Select value={value} onValueChange={onChange}>
            <SelectTrigger className={cn("w-[200px]", className)}>
                <SelectValue placeholder="Laboratorio" />
            </SelectTrigger>
            <SelectContent>
                {LABORATORIOS.map((lab) => (
                    <SelectItem key={lab.id} value={lab.id}>
                        {lab.label}
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}

export default LaboratorioSelect;
