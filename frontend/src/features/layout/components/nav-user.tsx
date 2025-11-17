"use client"

/**
 * Componente de usuario en sidebar
 * Integra el UserButton con dropdown y dialog de perfil estilo Clerk
 */

import { useState } from "react";
import { useSession, signOut } from "next-auth/react";
import {
  IconDotsVertical,
  IconLogout,
  IconUserCircle,
  IconShield,
} from "@tabler/icons-react"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { UserProfileDialog } from "@/features/auth/components/user-profile-dialog";

export function NavUser({
  user,
}: {
  user: {
    name: string
    email: string
    avatar?: string
  }
}) {
  const { isMobile } = useSidebar();
  const { data: session } = useSession();
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Obtener iniciales del nombre
  const getInitials = () => {
    return user.name.split(' ').map(n => n[0]).join('').toUpperCase()
  };

  // Obtener color del avatar basado en el rol
  const getAvatarColor = () => {
    const role = session?.user?.role?.toLowerCase();
    switch (role) {
      case "superadmin":
        return "bg-red-500";
      case "epidemiologo":
        return "bg-blue-500";
      default:
        return "bg-primary";
    }
  };

  const handleOpenProfile = () => {
    setDropdownOpen(false); // Cerrar el dropdown primero
    setShowProfileDialog(true);
  };

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar className={`h-8 w-8 rounded-lg ${getAvatarColor()}`}>
                  <AvatarImage src={user.avatar} alt={user.name} />
                  <AvatarFallback className="rounded-lg bg-transparent text-white">
                    {getInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{user.name}</span>
                  <span className="text-muted-foreground truncate text-xs">
                    {user.email}
                  </span>
                </div>
                <IconDotsVertical className="ml-auto size-4" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
              side={isMobile ? "bottom" : "right"}
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className={`h-8 w-8 rounded-lg ${getAvatarColor()}`}>
                    <AvatarImage src={user.avatar} alt={user.name} />
                    <AvatarFallback className="rounded-lg bg-transparent text-white">
                      {getInitials()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{user.name}</span>
                    <span className="text-muted-foreground truncate text-xs">
                      {user.email}
                    </span>
                    {session?.user?.role && (
                      <div className="flex items-center gap-1 mt-0.5">
                        <IconShield className="h-2.5 w-2.5 text-muted-foreground" />
                        <span className="text-[10px] text-muted-foreground capitalize">
                          {session.user.role}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleOpenProfile}
                className="cursor-pointer"
              >
                <IconUserCircle />
                Mi perfil
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => signOut({ callbackUrl: "/login" })}
                className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50 dark:focus:bg-red-950"
              >
                <IconLogout />
                Cerrar sesión
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>

      {/* Dialog de perfil estilo Clerk */}
      <UserProfileDialog
        open={showProfileDialog}
        onOpenChange={setShowProfileDialog}
      />
    </>
  )
}
