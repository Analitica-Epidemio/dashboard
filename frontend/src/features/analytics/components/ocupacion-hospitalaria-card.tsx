"use client";

/**
 * OcupacionHospitalariaCard Component
 *
 * Displays hospital bed occupancy data for IRA (Acute Respiratory Infections)
 * as a table grouped by establishment.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Building2, BedDouble } from "lucide-react";
import type { OcupacionCamasData } from "../api";

interface OcupacionHospitalariaCardProps {
  title: string;
  description?: string;
  data: OcupacionCamasData[];
  className?: string;
}

/**
 * Group data by establishment and get the latest value per establishment
 */
function aggregateByEstablishment(data: OcupacionCamasData[]) {
  const estMap = new Map<string, OcupacionCamasData>();

  // Group by establishment, keeping the latest week
  data.forEach((d) => {
    const existing = estMap.get(d.establecimiento_nombre);
    if (!existing || d.semana_epidemiologica > existing.semana_epidemiologica) {
      estMap.set(d.establecimiento_nombre, d);
    }
  });

  return Array.from(estMap.values()).sort(
    (a, b) => b.camas_ira - a.camas_ira
  );
}

export function OcupacionHospitalariaCard({
  title,
  description,
  data,
  className,
}: OcupacionHospitalariaCardProps) {
  const aggregatedData = aggregateByEstablishment(data);

  // Calculate totals
  const totalCamasIRA = aggregatedData.reduce((acc, d) => acc + d.camas_ira, 0);
  const totalCamasUTI = aggregatedData.reduce((acc, d) => acc + (d.camas_uti || 0), 0);

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              {title}
            </CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <BedDouble className="h-3 w-3" />
              {totalCamasIRA} camas IRA
            </Badge>
            {totalCamasUTI > 0 && (
              <Badge variant="secondary" className="flex items-center gap-1">
                {totalCamasUTI} UTI
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {aggregatedData.length === 0 ? (
          <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg">
            <p className="text-muted-foreground">No hay datos de hospitalización disponibles</p>
          </div>
        ) : (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Establecimiento</TableHead>
                  <TableHead className="text-right">Semana</TableHead>
                  <TableHead className="text-right">Camas IRA</TableHead>
                  {totalCamasUTI > 0 && (
                    <TableHead className="text-right">Camas UTI</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {aggregatedData.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">
                      {item.establecimiento_nombre}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      SE {item.semana_epidemiologica}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge
                        variant={item.camas_ira > 10 ? "destructive" : "secondary"}
                      >
                        {item.camas_ira}
                      </Badge>
                    </TableCell>
                    {totalCamasUTI > 0 && (
                      <TableCell className="text-right">
                        {item.camas_uti ? (
                          <Badge
                            variant={item.camas_uti > 5 ? "destructive" : "outline"}
                          >
                            {item.camas_uti}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {aggregatedData.length > 0 && (
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>{aggregatedData.length} establecimientos reportando</span>
            <span>Datos de la última semana con información</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
