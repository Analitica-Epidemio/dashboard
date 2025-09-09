/**
 * Collapsible Sidebar Component
 * Icon-only by default, expands on hover with floating overlay
 * Navigation only - matches AppSidebar items
 */

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  IconDashboard,
  IconListDetails,
  IconChartBar,
  IconFolder,
  IconUsers,
  IconSettings,
  IconHelp,
  IconSearch,
  IconInnerShadowTop,
  IconMenu2,
  IconChevronLeft,
  IconDatabase,
  IconReport,
  IconFileWord,
} from "@tabler/icons-react";

interface CollapsibleSidebarProps {
  className?: string;
}

interface NavItem {
  id: string;
  title: string;
  icon: React.ElementType;
  url: string;
  badge?: string;
}

// Main navigation items - matching AppSidebar
const navMain: NavItem[] = [
  {
    id: "dashboard",
    title: "Dashboard",
    icon: IconDashboard,
    url: "/dashboard",
  },
  {
    id: "eventos",
    title: "Eventos",
    icon: IconListDetails,
    url: "/dashboard/eventos",
  },
  {
    id: "analytics",
    title: "Analytics",
    icon: IconChartBar,
    url: "/analytics",
  },
  {
    id: "projects",
    title: "Projects",
    icon: IconFolder,
    url: "#",
  },
  {
    id: "team",
    title: "Team",
    icon: IconUsers,
    url: "#",
  },
];

// Documents section
const documents: NavItem[] = [
  {
    id: "data-library",
    title: "Data Library",
    icon: IconDatabase,
    url: "#",
  },
  {
    id: "reports",
    title: "Reports",
    icon: IconReport,
    url: "#",
  },
  {
    id: "word-assistant",
    title: "Word Assistant",
    icon: IconFileWord,
    url: "#",
  },
];

// Secondary navigation
const navSecondary: NavItem[] = [
  {
    id: "configuracion",
    title: "Configuración de Estrategias",
    icon: IconSettings,
    url: "/dashboard/estrategias",
  },
  {
    id: "help",
    title: "Get Help",
    icon: IconHelp,
    url: "#",
  },
  {
    id: "search",
    title: "Search",
    icon: IconSearch,
    url: "#",
  },
];

export const CollapsibleSidebar: React.FC<CollapsibleSidebarProps> = ({
  className,
}) => {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);

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

  const renderNavItem = (item: NavItem, showLabel: boolean) => {
    const Icon = item.icon;
    const isActive = isActiveRoute(item.url);

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
      {/* Backdrop overlay when expanded (not pinned) */}
      {isExpanded && !isPinned && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity duration-200"
          onClick={() => setIsExpanded(false)}
        />
      )}

      {/* Sidebar Container */}
      <TooltipProvider delayDuration={0}>
        <div
          className={cn(
            "fixed left-0 top-0 h-screen bg-white border-r border-gray-200 z-50",
            "transition-all duration-200 ease-in-out",
            isExpanded ? "w-72 shadow-2xl" : "w-14",
            className
          )}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="h-14 flex items-center justify-between px-3 border-b border-gray-200">
              {isExpanded ? (
                <>
                  <a href="#" className="flex items-center gap-2">
                    <IconInnerShadowTop className="h-5 w-5" />
                    <span className="text-base font-semibold">Acme Inc.</span>
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
                </>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 mx-auto"
                  onClick={() => setIsExpanded(!isExpanded)}
                >
                  <IconMenu2 className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto">
              <div className="py-2">
                {/* Main Navigation */}
                <div className="px-2 space-y-1">
                  {navMain.map((item) => renderNavItem(item, isExpanded))}
                </div>

                {/* Documents Section */}
                {isExpanded && (
                  <>
                    <Separator className="my-3" />
                    <div className="px-4 mb-2">
                      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Documents
                      </h3>
                    </div>
                  </>
                )}
                <div className="px-2 space-y-1">
                  {documents.map((item) => renderNavItem(item, isExpanded))}
                </div>
              </div>
            </div>

            {/* Bottom Section */}
            <div className="border-t border-gray-200">
              <div className="py-2 px-2 space-y-1">
                {navSecondary.map((item) => renderNavItem(item, isExpanded))}
              </div>

              {/* User Section */}
              <div className="p-2 border-t border-gray-200">
                {isExpanded ? (
                  <div className="flex items-center gap-2 px-2 py-1.5">
                    <div className="h-7 w-7 rounded-full bg-gray-300" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">shadcn</p>
                      <p className="text-xs text-gray-500 truncate">
                        m@example.com
                      </p>
                    </div>
                  </div>
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="h-8 w-8 rounded-full bg-gray-300 mx-auto cursor-pointer" />
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <div>
                        <p className="text-sm font-medium">shadcn</p>
                        <p className="text-xs text-gray-500">m@example.com</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>
          </div>
        </div>
      </TooltipProvider>
    </>
  );
};
