"use client"
import React, { useState, useCallback, createContext, ReactNode } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu"
import { string } from "zod";

type tipoENO = {
    nombre: string
}

type grupoENO = {
    nombre: string
}


export default function Page(){
    const [gruposENO, setGrupos] = useState<grupoENO[]>([])
    const [tiposENO, setTipos] = useState<tipoENO[]>([])
    const [seleccion, setSeleccion] = useState<{ tipo: "grupoENO" | "tipoENO" | null; valor: string | null }>({
    tipo: null,
    valor: null,
  })
    return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <div className="flex flex-col min-h-screen bg-background">
            <div className="flex justify-center items-center h-screen">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                    <Button variant="outline">Elegir opción</Button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent>
                    {/* Primera lista */}
                    <DropdownMenuLabel>Categorías ENO</DropdownMenuLabel>
                    {gruposENO.map((grupo) => (
                        <DropdownMenuItem
                        key={grupo.nombre}
                        onClick={() => alert(`Elegiste categoría: ${grupo.nombre}`)}
                        >
                        {grupo.nombre}
                        </DropdownMenuItem>
                    ))}

                    <DropdownMenuSeparator />

                    {/* Segunda lista */}
                    <DropdownMenuLabel>ENO específicos</DropdownMenuLabel>
                    {tiposENO.map((tipo) => (
                        <DropdownMenuItem
                        key={tipo.nombre}
                        onClick={() => alert(`Elegiste evento: ${tipo.nombre}`)}
                        >
                        {tipo.nombre}
                        </DropdownMenuItem>
                    ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}