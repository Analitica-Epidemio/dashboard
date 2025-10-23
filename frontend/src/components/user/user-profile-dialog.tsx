"use client";

/**
 * Dialog de perfil de usuario estilo Clerk
 * Layout: Sidebar izquierdo con navegación, contenido principal derecha
 * Subcomponentes separados para mejor mantenibilidad
 */

import { User, Lock } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUserProfile } from "@/lib/api/hooks/use-user";
import { ProfileInfoSection } from "./profile-sections/profile-info-section";
import { EmailSection } from "./profile-sections/email-section";
import { AccountInfoSection } from "./profile-sections/account-info-section";
import { PasswordSection } from "./security-sections/password-section";
import { ActiveSessions } from "@/components/sessions/active-sessions";

interface UserProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UserProfileDialog({ open, onOpenChange }: UserProfileDialogProps) {
  const { data: profile, isLoading: loading } = useUserProfile();

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange} modal={true}>
        <DialogContent className="sm:max-w-[90vw] md:max-w-[800px] lg:max-w-[900px] h-[90vh] p-0 gap-0 overflow-hidden">
          <div className="flex items-center justify-center h-full">
            <p className="text-base font-bold">Cargando perfil...</p>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!profile) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange} modal={true}>
      <DialogContent className="sm:max-w-[90vw] md:max-w-[800px] lg:max-w-[900px] h-[90vh] p-0 gap-0 overflow-hidden">
        <Tabs defaultValue="profile" className="flex h-full">
          {/* Sidebar izquierdo - Navegación */}
          <div className="w-[244px] flex flex-col shrink-0 border-r py-6 px-4">
            <div className="mb-6">
              <h1 className="text-base font-bold mb-1">Cuenta</h1>
              <p className="text-sm text-muted-foreground">
                Administra la información de tu cuenta
              </p>
            </div>

            <TabsList className="flex flex-col h-auto w-full bg-transparent p-0 gap-0">
              <TabsTrigger
                value="profile"
                className="w-full h-8 justify-start px-4 rounded-md text-sm font-normal data-[state=active]:bg-accent data-[state=active]:text-foreground data-[state=inactive]:bg-transparent hover:bg-accent/50 transition-colors"
              >
                <User className="h-4 w-4 mr-2 shrink-0" />
                Perfil
              </TabsTrigger>
              <TabsTrigger
                value="security"
                className="w-full h-8 justify-start px-4 rounded-md text-sm font-normal data-[state=active]:bg-accent data-[state=active]:text-foreground data-[state=inactive]:bg-transparent hover:bg-accent/50 transition-colors"
              >
                <Lock className="h-4 w-4 mr-2 shrink-0" />
                Seguridad
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Área de contenido principal - Derecha */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Tab: Perfil */}
            <TabsContent value="profile" className="m-0 space-y-0">
              <h2 className="text-base font-bold mb-4">Detalles del perfil</h2>

              <ProfileInfoSection
                profile={{
                  nombre: profile.nombre,
                  apellido: profile.apellido,
                }}
              />

              <EmailSection email={profile.email} />

              <AccountInfoSection
                createdAt={profile.created_at}
                lastLogin={profile.last_login}
                role={profile.role}
              />
            </TabsContent>

            {/* Tab: Seguridad */}
            <TabsContent value="security" className="m-0 space-y-0">
              <h2 className="text-base font-bold mb-4">Seguridad</h2>

              <PasswordSection />

              {/* Sección: Sesiones activas */}
              <div className="flex flex-row-reverse items-start border-t pt-4 pb-4 gap-6">
                <div className="flex-shrink-0"></div>
                <div className="flex flex-col gap-3 min-w-0 w-full">
                  <h3 className="text-sm font-medium">Sesiones activas</h3>
                  <ActiveSessions />
                </div>
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
