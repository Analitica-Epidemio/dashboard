"use client";

import { Settings, Trash2, GripVertical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface WidgetContainerProps {
  title?: string | null;
  showTitle?: boolean;
  isLoading?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function WidgetContainer({
  title,
  showTitle = true,
  isLoading = false,
  onEdit,
  onDelete,
  children,
  className,
}: WidgetContainerProps) {
  return (
    <Card className={cn("h-full flex flex-col", className)}>
      {showTitle && (title || onEdit || onDelete) && (
        <CardHeader className="pb-3 flex-none">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              <GripVertical className="w-4 h-4 text-muted-foreground cursor-grab" />
              {title && <CardTitle className="text-sm font-medium">{title}</CardTitle>}
            </div>
            <div className="flex items-center gap-1">
              {onEdit && (
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onEdit}>
                  <Settings className="w-3.5 h-3.5" />
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive hover:text-destructive"
                  onClick={onDelete}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      )}
      <CardContent className="flex-1 flex flex-col min-h-0">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
