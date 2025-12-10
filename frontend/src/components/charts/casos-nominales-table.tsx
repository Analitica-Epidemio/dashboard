"use client";

import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { ArrowUpDown, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface CasosNominalesTableProps {
    data: Array<{
        id: string | number;
        fechaInicio: string;
        clasificacion: string;
        sexo?: string;
        edad?: number;
        provincia?: string;
        hospitalizado?: boolean;
        fallecido?: boolean;
    }>;
    onRowClick?: (id: string | number) => void;
    className?: string;
}

type SortField = "id" | "fechaInicio" | "clasificacion" | "edad";
type SortDirection = "asc" | "desc";

function ClasificacionBadge({ clasificacion }: { clasificacion: string }) {
    const variants: Record<string, { variant: "default" | "destructive" | "secondary" | "outline"; label: string }> = {
        confirmado: { variant: "destructive", label: "Confirmado" },
        probable: { variant: "default", label: "Probable" },
        sospechoso: { variant: "secondary", label: "Sospechoso" },
        descartado: { variant: "outline", label: "Descartado" },
    };

    const config = variants[clasificacion.toLowerCase()] || { variant: "outline", label: clasificacion };

    return <Badge variant={config.variant}>{config.label}</Badge>;
}

export function CasosNominalesTable({ data, onRowClick, className }: CasosNominalesTableProps) {
    const [sortField, setSortField] = useState<SortField>("fechaInicio");
    const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc");
        } else {
            setSortField(field);
            setSortDirection("desc");
        }
    };

    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => {
            let aVal: string | number;
            let bVal: string | number;

            switch (sortField) {
                case "id":
                    aVal = typeof a.id === 'number' ? a.id : String(a.id);
                    bVal = typeof b.id === 'number' ? b.id : String(b.id);
                    break;
                case "fechaInicio":
                    aVal = a.fechaInicio;
                    bVal = b.fechaInicio;
                    break;
                case "clasificacion":
                    aVal = a.clasificacion;
                    bVal = b.clasificacion;
                    break;
                case "edad":
                    aVal = a.edad ?? 0;
                    bVal = b.edad ?? 0;
                    break;
                default:
                    return 0;
            }

            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
            }

            const strA = String(aVal);
            const strB = String(bVal);
            return sortDirection === "asc" ? strA.localeCompare(strB) : strB.localeCompare(strA);
        });
    }, [data, sortField, sortDirection]);

    const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) {
            return <ArrowUpDown className="ml-2 h-4 w-4" />;
        }
        return sortDirection === "asc" ? (
            <ChevronUp className="ml-2 h-4 w-4" />
        ) : (
            <ChevronDown className="ml-2 h-4 w-4" />
        );
    };

    return (
        <div className={cn("rounded-md border", className)}>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>
                            <Button variant="ghost" size="sm" className="-ml-4" onClick={() => handleSort("id")}>
                                ID
                                <SortIcon field="id" />
                            </Button>
                        </TableHead>
                        <TableHead>
                            <Button variant="ghost" size="sm" onClick={() => handleSort("fechaInicio")}>
                                F. Inicio
                                <SortIcon field="fechaInicio" />
                            </Button>
                        </TableHead>
                        <TableHead>
                            <Button variant="ghost" size="sm" onClick={() => handleSort("clasificacion")}>
                                Clasificación
                                <SortIcon field="clasificacion" />
                            </Button>
                        </TableHead>
                        <TableHead>Sexo</TableHead>
                        <TableHead className="text-right">
                            <Button variant="ghost" size="sm" onClick={() => handleSort("edad")}>
                                Edad
                                <SortIcon field="edad" />
                            </Button>
                        </TableHead>
                        <TableHead>Provincia</TableHead>
                        <TableHead className="text-center">Hosp.</TableHead>
                        <TableHead className="text-center">Fall.</TableHead>
                        <TableHead></TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {sortedData.map((row) => (
                        <TableRow
                            key={row.id}
                            className={cn(onRowClick && "cursor-pointer hover:bg-muted/50")}
                            onClick={() => onRowClick?.(row.id)}
                        >
                            <TableCell className="font-mono text-sm">{row.id}</TableCell>
                            <TableCell>{row.fechaInicio}</TableCell>
                            <TableCell>
                                <ClasificacionBadge clasificacion={row.clasificacion} />
                            </TableCell>
                            <TableCell>{row.sexo || "-"}</TableCell>
                            <TableCell className="text-right tabular-nums">{row.edad ?? "-"}</TableCell>
                            <TableCell className="max-w-[120px] truncate" title={row.provincia}>
                                {row.provincia || "-"}
                            </TableCell>
                            <TableCell className="text-center">
                                {row.hospitalizado ? (
                                    <Badge variant="secondary" className="bg-amber-100 text-amber-800">Sí</Badge>
                                ) : (
                                    <span className="text-muted-foreground">No</span>
                                )}
                            </TableCell>
                            <TableCell className="text-center">
                                {row.fallecido ? (
                                    <Badge variant="destructive">Sí</Badge>
                                ) : (
                                    <span className="text-muted-foreground">No</span>
                                )}
                            </TableCell>
                            <TableCell>
                                {onRowClick && (
                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                        <ExternalLink className="h-4 w-4" />
                                    </Button>
                                )}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

export default CasosNominalesTable;
