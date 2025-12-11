"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const TECNICAS = [
    { id: "pcr", label: "PCR", description: "Reacción en cadena de polimerasa" },
    { id: "if", label: "IF", description: "Inmunofluorescencia" },
    { id: "cultivo", label: "Cultivo", description: "Cultivo viral" },
    { id: "serologia", label: "Serología", description: "Detección de anticuerpos" },
    { id: "antigeno", label: "Antígeno", description: "Test rápido de antígeno" },
];

interface TecnicaFilterProps {
    value: string[];
    onChange: (value: string[]) => void;
    className?: string;
}

export function TecnicaFilter({ value, onChange, className }: TecnicaFilterProps) {
    const handleToggle = (tecnicaId: string, checked: boolean) => {
        if (checked) {
            onChange([...value, tecnicaId]);
        } else {
            onChange(value.filter((id) => id !== tecnicaId));
        }
    };

    return (
        <div className={cn("space-y-3", className)}>
            <Label className="text-sm font-medium">Técnica</Label>
            <div className="flex flex-wrap gap-4">
                {TECNICAS.map((tecnica) => (
                    <div key={tecnica.id} className="flex items-center gap-2">
                        <Checkbox
                            id={`tecnica-${tecnica.id}`}
                            checked={value.includes(tecnica.id)}
                            onCheckedChange={(checked) => handleToggle(tecnica.id, !!checked)}
                        />
                        <Label
                            htmlFor={`tecnica-${tecnica.id}`}
                            className="text-sm cursor-pointer"
                            title={tecnica.description}
                        >
                            {tecnica.label}
                        </Label>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default TecnicaFilter;
