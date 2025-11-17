"use client"

import * as React from "react"
import Link from "next/link"
import { IconInnerShadowTop } from "@tabler/icons-react"
import { navigationConfig, getNavigationItems } from "../navigation-config"
import { useUserProfile } from "@/features/auth/api"

import { NavMain } from "./nav-main"
import { NavUser } from "./nav-user"
import { Button } from "@/components/ui/button"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"


export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const navItems = getNavigationItems();
  const { data: user } = useUserProfile();

  const userData = {
    name: (user?.nombre || user?.apellido) ? `${user?.nombre || ''} ${user?.apellido || ''}`.trim() : "Usuario",
    email: user?.email || "usuario@epidemio.com",
    avatar: "/avatars/default.jpg",
  };

  const primaryAction = navigationConfig.primaryAction;

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href="/dashboard">
                <IconInnerShadowTop className="!size-5" />
                <span className="text-base font-semibold">{navigationConfig.appName}</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* Botón primario: Subir Archivo */}
        <div className="px-2 py-2">
          <Button asChild className="w-full" size="sm">
            <Link href={primaryAction.url}>
              <primaryAction.icon className="h-4 w-4 mr-2" />
              {primaryAction.title}
            </Link>
          </Button>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navItems} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={userData} />
      </SidebarFooter>
    </Sidebar>
  )
}
