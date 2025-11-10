"use client"

import { type Icon } from "@tabler/icons-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url?: string
    icon?: Icon | React.ElementType
    type?: "separator" | "link" | "header"
  }[]
}) {
  const pathname = usePathname()

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-1">
        <SidebarMenu>
          {items.map((item, index) => {
            // Header de sección
            if (item.type === "header") {
              return (
                <div
                  key={item.id || `header-${index}`}
                  className="px-3 pt-4 pb-1 first:pt-0"
                >
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {item.title}
                  </h3>
                </div>
              )
            }

            // Separador (deprecated, usar headers)
            if (item.type === "separator") {
              return (
                <div key={item.id || `separator-${index}`} className="my-2">
                  <div className="border-t border-sidebar-border" />
                </div>
              )
            }

            // Link normal
            if (!item.url) return null;

            // Check if current path matches or starts with the item URL
            const isActive = pathname === item.url ||
                           (item.url !== '/dashboard' && pathname.startsWith(item.url))

            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  asChild
                  tooltip={item.title}
                  isActive={isActive}
                >
                  <Link href={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
