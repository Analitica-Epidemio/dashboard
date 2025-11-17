"use client";

import { useState, useEffect } from "react";
import GridLayout from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import { Widget } from "./widgets/types";
import { WidgetRenderer } from "./widgets/widget-renderer";

interface LayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
}

interface BoletinCanvasProps {
  widgets: Widget[];
  onLayoutChange: (layout: LayoutItem[]) => void;
  onDeleteWidget: (id: string) => void;
}

export function BoletinCanvas({ widgets, onLayoutChange, onDeleteWidget }: BoletinCanvasProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Convert widgets to react-grid-layout format
  const layout = widgets.map((widget) => ({
    i: widget.id,
    x: widget.position.x,
    y: widget.position.y,
    w: widget.position.w,
    h: widget.position.h,
    minW: 2,
    minH: 2,
  }));

  const handleLayoutChange = (newLayout: LayoutItem[]) => {
    onLayoutChange(newLayout);
  };

  if (!mounted) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Cargando editor...
      </div>
    );
  }

  if (widgets.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px] text-center">
        <div className="max-w-md p-8">
          <h3 className="text-lg font-semibold mb-2">Canvas Vacío</h3>
          <p className="text-sm text-muted-foreground">
            Comienza agregando widgets desde la biblioteca de la izquierda. Arrastra y suelta
            para reorganizar el layout.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={40}
        width={1200}
        onLayoutChange={handleLayoutChange}
        isDraggable={true}
        isResizable={true}
        compactType="vertical"
        preventCollision={false}
        margin={[16, 16]}
        containerPadding={[0, 0]}
      >
        {widgets.map((widget) => (
          <div key={widget.id} className="widget-item">
            <WidgetRenderer
              widget={widget}
              onDelete={() => onDeleteWidget(widget.id)}
            />
          </div>
        ))}
      </GridLayout>

      <style jsx global>{`
        .react-grid-layout {
          position: relative;
        }

        .react-grid-item {
          transition: all 200ms ease;
          transition-property: left, top;
        }

        .react-grid-item.react-grid-placeholder {
          background: hsl(var(--primary) / 0.2);
          opacity: 0.2;
          border: 2px dashed hsl(var(--primary));
          border-radius: 8px;
          transition-duration: 100ms;
          z-index: 2;
        }

        .react-grid-item > .react-resizable-handle {
          position: absolute;
          width: 20px;
          height: 20px;
        }

        .react-grid-item > .react-resizable-handle::after {
          content: "";
          position: absolute;
          right: 3px;
          bottom: 3px;
          width: 8px;
          height: 8px;
          border-right: 2px solid hsl(var(--muted-foreground) / 0.4);
          border-bottom: 2px solid hsl(var(--muted-foreground) / 0.4);
        }

        .react-grid-item.react-dragging {
          transition: none;
          z-index: 100;
          will-change: transform;
        }

        .react-grid-item.cssTransforms {
          transition-property: transform;
        }

        .react-grid-item.resizing {
          transition: none;
          z-index: 100;
          will-change: width, height;
        }

        .widget-item {
          height: 100%;
        }
      `}</style>
    </div>
  );
}
