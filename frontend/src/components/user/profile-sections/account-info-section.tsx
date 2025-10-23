"use client";

/**
 * Sección de información de cuenta
 * Muestra fechas y rol
 */

import { format } from "date-fns";
import { es } from "date-fns/locale";
import { Calendar, Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface AccountInfoSectionProps {
  createdAt: string;
  lastLogin?: string | null;
  role: string;
}

export function AccountInfoSection({ createdAt, lastLogin, role }: AccountInfoSectionProps) {
  const getRoleBadgeColor = (roleValue: string) => {
    switch (roleValue.toLowerCase()) {
      case 'superadmin':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'epidemiologo':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="flex flex-row-reverse items-start border-t pt-4 pb-4 gap-6">
      <div className="flex-shrink-0"></div>
      <div className="flex flex-col gap-2 min-w-0 w-full">
        <h3 className="text-sm font-medium">Información de cuenta</h3>
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span>
              Cuenta creada:{" "}
              {format(new Date(createdAt), "dd MMM yyyy", { locale: es })}
            </span>
          </div>
          {lastLogin && (
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span>
                Último acceso:{" "}
                {format(new Date(lastLogin), "dd MMM yyyy, HH:mm", {
                  locale: es,
                })}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 mt-2">
            <Badge className={getRoleBadgeColor(role)} variant="outline">
              {role}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
}
