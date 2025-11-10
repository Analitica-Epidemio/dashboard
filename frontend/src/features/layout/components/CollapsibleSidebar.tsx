/**
 * Collapsible Sidebar Component
 * Icon-only by default, expands on hover with floating overlay
 * Navigation only - uses shared configuration
 */

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  IconInnerShadowTop,
  IconMenu2,
  IconChevronLeft,
} from "@tabler/icons-react";
import { navigationConfig, getNavigationItems } from "../navigation-config";
import { useAuth } from "@/features/auth/hooks";

interface CollapsibleSidebarProps {
  className?: string;
}


export const CollapsibleSidebar: React.FC<CollapsibleSidebarProps> = ({
  className,
}) => {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);

  const navItems = getNavigationItems();
  const { user } = useAuth();

  const userData = {
    name: user?.name || "Usuario",
    email: user?.email || "usuario@epidemio.com",
    avatar: user?.image || "/avatars/default.jpg",
  };

  // Clear timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
      }
    };
  }, [hoverTimeout]);

  const handleMouseEnter = () => {
    if (!isPinned) {
      // Small delay before expanding to prevent accidental triggers
      const timeout = setTimeout(() => {
        setIsExpanded(true);
      }, 150);
      setHoverTimeout(timeout);
    }
  };

  const handleMouseLeave = () => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }

    if (!isPinned) {
      setIsExpanded(false);
    }
  };

  const togglePin = () => {
    setIsPinned(!isPinned);
    if (!isPinned) {
      setIsExpanded(true);
    }
  };

  const isActiveRoute = (url: string) => {
    if (url === "#") return false;
    return pathname.startsWith(url);
  };

  const renderNavItem = (item: typeof navItems[0], showLabel: boolean) => {
    // Headers en la vista expandida
    if (item.type === "header" && showLabel) {
      return (
        <div
          key={item.id}
          className="px-3 pt-4 pb-1 first:pt-0"
        >
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {item.title}
          </h3>
        </div>
      );
    }

    // Skip headers en la vista colapsada (no tienen icon)
    if (item.type === "header" || !item.icon) {
      return null;
    }

    const Icon = item.icon;
    const isActive = isActiveRoute(item.url || "#");

    if (showLabel) {
      return (
        <a
          key={item.id}
          href={item.url}
          className={cn(
            "flex items-center justify-between px-3 py-2 rounded-lg",
            "hover:bg-gray-100 transition-colors",
            isActive && "bg-blue-50 text-blue-600 hover:bg-blue-100"
          )}
        >
          <div className="flex items-center gap-3">
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm font-medium">{item.title}</span>
          </div>
          {item.badge && (
            <Badge variant="secondary" className="text-xs">
              {item.badge}
            </Badge>
          )}
        </a>
      );
    }

    return (
      <Tooltip key={item.id}>
        <TooltipTrigger asChild>
          <a
            href={item.url}
            className={cn(
              "flex items-center justify-center p-2 rounded-lg",
              "hover:bg-gray-100 transition-colors",
              isActive && "bg-blue-50 text-blue-600 hover:bg-blue-100"
            )}
          >
            <Icon className="h-5 w-5" />
          </a>
        </TooltipTrigger>
        <TooltipContent side="right" className="flex items-center gap-2">
          {item.title}
          {item.badge && (
            <Badge variant="secondary" className="text-xs ml-1">
              {item.badge}
            </Badge>
          )}
        </TooltipContent>
      </Tooltip>
    );
  };

  return (
    <>
      {/* Base sidebar (always visible, takes space in layout) */}
      <div className={cn("relative w-14 h-screen flex-shrink-0", className)}>
        <div className="w-14 h-full bg-white border-r border-gray-200">
          <div className="flex flex-col h-full">
            {/* Collapsed Header */}
            <div className="h-14 flex items-center justify-center border-b border-gray-200">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                <IconMenu2 className="h-4 w-4" />
              </Button>
            </div>

            {/* Collapsed Navigation */}
            <div className="flex-1 overflow-y-auto py-2">
              <TooltipProvider delayDuration={0}>
                <div className="px-2 space-y-1">
                  {navItems.map((item) => renderNavItem(item, false))}
                </div>
              </TooltipProvider>
            </div>

            {/* Collapsed User Section */}
            <div className="border-t border-gray-200 p-2">
              <TooltipProvider delayDuration={0}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="h-8 w-8 rounded-full bg-gray-300 mx-auto cursor-pointer" />
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <div>
                      <p className="text-sm font-medium">{userData.name}</p>
                      <p className="text-xs text-gray-500">{userData.email}</p>
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      </div>

      {/* Backdrop overlay when expanded (not pinned) */}
      {isExpanded && !isPinned && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity duration-200"
          onClick={() => setIsExpanded(false)}
        />
      )}

      {/* Expanded overlay (absolute positioned) */}
      {isExpanded && (
        <div
          className={cn(
            "fixed left-0 top-0 h-screen bg-white border-r border-gray-200 z-50",
            "transition-all duration-200 ease-in-out",
            "w-72 shadow-2xl"
          )}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="flex flex-col h-full">
            {/* Expanded Header */}
            <div className="h-14 flex items-center justify-between px-3 border-b border-gray-200">
              <a href="/dashboard" className="flex items-center gap-2">
                <IconInnerShadowTop className="h-5 w-5" />
                <span className="text-base font-semibold">{navigationConfig.appName}</span>
              </a>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={togglePin}
              >
                <IconChevronLeft
                  className={cn(
                    "h-4 w-4 transition-transform",
                    isPinned && "rotate-180"
                  )}
                />
              </Button>
            </div>

            {/* Expanded Main Content */}
            <div className="flex-1 overflow-y-auto">
              <div className="py-2">
                <div className="px-2 space-y-1">
                  {navItems.map((item) => renderNavItem(item, true))}
                </div>
              </div>
            </div>

            {/* Expanded User Section */}
            <div className="border-t border-gray-200">
              <div className="p-2">
                <div className="flex items-center gap-2 px-2 py-1.5">
                  <div className="h-7 w-7 rounded-full bg-gray-300" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{userData.name}</p>
                    <p className="text-xs text-gray-500 truncate">
                      {userData.email}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
