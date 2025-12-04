"use client";

import { AppSidebar } from "@/features/layout/components";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { FileText } from "lucide-react";
import { BoletinGenerator } from "@/features/boletines/components/nuevo/boletin-generator";

export default function NuevoBoletinPage() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink href="/dashboard/boletines">
                  Boletines
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                <BreadcrumbPage>Nuevo Boletín</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <div className="flex flex-1 flex-col overflow-auto">
          <div className="flex-1 space-y-6 p-4 md:p-6 max-w-4xl mx-auto w-full">
            {/* Header */}
            <div>
              <div className="flex items-center gap-2">
                <FileText className="h-6 w-6" />
                <h1 className="text-2xl font-bold">Generar Boletín Epidemiológico</h1>
              </div>
              <p className="text-muted-foreground mt-1">
                Selecciona el período y las secciones a incluir. Los datos se cargarán
                automáticamente de la base de datos.
              </p>
            </div>

            {/* Generator Component */}
            <BoletinGenerator />
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
