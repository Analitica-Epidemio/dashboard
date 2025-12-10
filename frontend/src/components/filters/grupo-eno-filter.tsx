"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const GRUPOS_ENO = [
    { id: "respiratorias", label: "Respiratorias", description: "ETI, IRAG, Neumonía" },
    { id: "vectoriales", label: "Vectoriales", description: "Dengue, Chikungunya, Zika" },
    { id: "inmunoprevenibles", label: "Inmunoprevenibles", description: "Sarampión, Rubeola" },
    { id: "entericas", label: "Entéricas", description: "Diarreas, Hepatitis A" },
    { id: "zoonoticas", label: "Zoonóticas", description: "Leptospirosis, Hantavirus" },
];

interface GrupoEnoFilterProps {
    value: string[];
    onChange: (value: string[]) => void;
    className?: string;
}

export function GrupoEnoFilter({ value, onChange, className }: GrupoEnoFilterProps) {
    const handleToggle = (grupoId: string, checked: boolean) => {
        if (checked) {
            onChange([...value, grupoId]);
        } else {
            onChange(value.filter((id) => id !== grupoId));
        }
    };

    return (
        <div className={cn("space-y-3", className)}>
            <Label className="text-sm font-medium">Grupo ENO</Label>
            <div className="space-y-2">
                {GRUPOS_ENO.map((grupo) => (
                    <div key={grupo.id} className="flex items-start gap-2">
                        <Checkbox
                            id={`grupo-${grupo.id}`}
                            checked={value.includes(grupo.id)}
                            onCheckedChange={(checked) => handleToggle(grupo.id, !!checked)}
                        />
                        <div className="grid gap-0.5 leading-none">
                            <Label
                                htmlFor={`grupo-${grupo.id}`}
                                className="text-sm font-medium cursor-pointer"
                            >
                                {grupo.label}
                            </Label>
                            <span className="text-xs text-muted-foreground">
                                {grupo.description}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default GrupoEnoFilter;
