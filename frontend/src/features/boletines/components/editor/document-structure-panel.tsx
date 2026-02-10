"use client";

/**
 * Panel de estructura del documento
 * Muestra un árbol navegable del contenido del boletín
 * + propiedades de elementos no-texto (charts, dynamic blocks, images, tables)
 */

import { useState, useMemo, useCallback, useEffect } from "react";
import type { Editor, JSONContent } from "@tiptap/react";
import {
  FileText,
  Heading1,
  Heading2,
  Heading3,
  Image,
  Table,
  BarChart3,
  ChevronRight,
  ChevronDown,
  SplitSquareVertical,
  Type,
  List,
  Palette,
  Trash2,
  Pencil,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

type SelectedElementType = "none" | "chart" | "dynamicBlock" | "dynamicTable" | "image";

interface SelectedElement {
  type: SelectedElementType;
  attrs?: Record<string, unknown>;
}

interface DocumentStructurePanelProps {
  editor: Editor | null;
  className?: string;
}

interface TreeNode {
  id: string;
  type: string;
  label: string;
  level?: number;
  children: TreeNode[];
  pos: number; // Position in the document for navigation
  nodeType: string;
}

/**
 * Build a tree structure from TipTap JSON content
 */
function buildDocumentTree(content: JSONContent): TreeNode[] {
  // First pass: collect all relevant nodes as a flat list
  const flatNodes: TreeNode[] = [];
  let nodeId = 0;
  let currentPos = 0;

  if (content.content) {
    for (const node of content.content) {
      const id = `node-${nodeId++}`;
      const pos = currentPos;

      // Calculate node size for position tracking
      const nodeSize = node.content
        ? node.content.reduce((acc, child) => {
            if (child.type === "text" && child.text) {
              return acc + child.text.length;
            }
            return acc + 2;
          }, 2)
        : node.text
          ? node.text.length
          : 1;

      let treeNode: TreeNode | null = null;

      switch (node.type) {
        case "heading": {
          const level = (node.attrs?.level as number) || 1;
          const text = extractText(node);
          treeNode = { id, type: "heading", label: text || `Título H${level}`, level, children: [], pos, nodeType: `h${level}` };
          break;
        }
        case "paragraph": {
          const text = extractText(node);
          if (text && text.length > 0) {
            treeNode = { id, type: "paragraph", label: text.slice(0, 50) + (text.length > 50 ? "..." : ""), children: [], pos, nodeType: "paragraph" };
          }
          break;
        }
        case "bulletList":
        case "orderedList": {
          const itemCount = node.content?.length || 0;
          treeNode = { id, type: node.type, label: `Lista (${itemCount} ${itemCount === 1 ? "item" : "items"})`, children: [], pos, nodeType: node.type };
          break;
        }
        case "table": {
          const rowCount = node.content?.length || 0;
          treeNode = { id, type: "table", label: `Tabla (${rowCount} ${rowCount === 1 ? "fila" : "filas"})`, children: [], pos, nodeType: "table" };
          break;
        }
        case "image":
          treeNode = { id, type: "image", label: "Imagen", children: [], pos, nodeType: "image" };
          break;
        case "dynamicChart": {
          const title = (node.attrs?.title as string) || "Gráfico dinámico";
          treeNode = { id, type: "chart", label: title, children: [], pos, nodeType: "dynamicChart" };
          break;
        }
        case "dynamicTable": {
          const title = (node.attrs?.title as string) || "Tabla dinámica";
          treeNode = { id, type: "dynamicTable", label: title, children: [], pos, nodeType: "dynamicTable" };
          break;
        }
        case "dynamicBlock": {
          const blockType = (node.attrs?.blockType as string) || "block";
          const title = (node.attrs?.config as { titulo?: string })?.titulo || blockType;
          treeNode = { id, type: "dynamicBlock", label: title, children: [], pos, nodeType: "dynamicBlock" };
          break;
        }
        case "pageBreak":
          treeNode = { id, type: "pageBreak", label: "Salto de página", children: [], pos, nodeType: "pageBreak" };
          break;
      }

      currentPos += nodeSize;
      if (treeNode) flatNodes.push(treeNode);
    }
  }

  // Second pass: build hierarchical tree based on heading levels
  // H1 contains everything until next H1
  // H2 contains everything until next H2 or H1
  // H3 contains everything until next H3, H2, or H1
  // Non-heading nodes become children of the nearest preceding heading
  const root: TreeNode[] = [];
  const stack: TreeNode[] = []; // stack of open heading ancestors

  for (const node of flatNodes) {
    if (node.type === "heading" && node.level) {
      // Pop headings from stack that are same level or deeper
      while (stack.length > 0 && (stack[stack.length - 1].level ?? 0) >= node.level) {
        stack.pop();
      }

      if (stack.length > 0) {
        // Nest under parent heading
        stack[stack.length - 1].children.push(node);
      } else {
        // Top-level heading
        root.push(node);
      }

      stack.push(node);
    } else {
      // Non-heading: attach as child of current heading
      if (stack.length > 0) {
        stack[stack.length - 1].children.push(node);
      } else {
        root.push(node);
      }
    }
  }

  return root;
}

/**
 * Extract text from a TipTap node
 */
function extractText(node: JSONContent): string {
  if (node.text) return node.text;
  if (!node.content) return "";
  return node.content.map(extractText).join("");
}

/**
 * Get icon for node type
 */
function getNodeIcon(type: string, level?: number) {
  switch (type) {
    case "heading":
      if (level === 1) return Heading1;
      if (level === 2) return Heading2;
      return Heading3;
    case "paragraph":
      return Type;
    case "bulletList":
    case "orderedList":
      return List;
    case "table":
    case "dynamicTable":
      return Table;
    case "image":
      return Image;
    case "chart":
    case "dynamicChart":
    case "dynamicBlock":
      return BarChart3;
    case "pageBreak":
      return SplitSquareVertical;
    default:
      return FileText;
  }
}

export function DocumentStructurePanel({ editor, className }: DocumentStructurePanelProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedElement, setSelectedElement] = useState<SelectedElement>({ type: "none" });

  // Build tree from editor content
  const tree = useMemo(() => {
    if (!editor) return [];
    const json = editor.getJSON();
    return buildDocumentTree(json);
  }, [editor?.state.doc]);

  // Expand all by default
  useEffect(() => {
    if (tree.length > 0 && expanded.size === 0) {
      const allIds = new Set(tree.map((n) => n.id));
      setExpanded(allIds);
    }
  }, [tree, expanded.size]);

  // Track editor selection for non-text element properties
  useEffect(() => {
    if (!editor) return;

    const updateSelection = () => {
      const { selection, doc } = editor.state;
      const node = doc.nodeAt(selection.from);

      if (!node) {
        setSelectedElement({ type: "none" });
        return;
      }

      switch (node.type.name) {
        case "dynamicChart":
          setSelectedElement({ type: "chart", attrs: node.attrs });
          break;
        case "dynamicBlock":
          setSelectedElement({ type: "dynamicBlock", attrs: node.attrs });
          break;
        case "dynamicTable":
          setSelectedElement({ type: "dynamicTable", attrs: node.attrs });
          break;
        case "image":
          setSelectedElement({ type: "image", attrs: node.attrs });
          break;
        default:
          setSelectedElement({ type: "none" });
      }
    };

    editor.on("selectionUpdate", updateSelection);
    editor.on("transaction", updateSelection);
    updateSelection();

    return () => {
      editor.off("selectionUpdate", updateSelection);
      editor.off("transaction", updateSelection);
    };
  }, [editor]);

  const toggleExpanded = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleNodeClick = useCallback(
    (node: TreeNode) => {
      setSelectedId(node.id);

      // Navigate to the position in the editor
      if (editor) {
        editor.chain().focus().setTextSelection(node.pos).run();

        // Try to scroll the element into view
        const { view } = editor;
        const coords = view.coordsAtPos(node.pos);
        if (coords) {
          const editorElement = view.dom.closest(".overflow-y-auto");
          if (editorElement) {
            const editorRect = editorElement.getBoundingClientRect();
            const scrollTop = coords.top - editorRect.top - 100;
            editorElement.scrollBy({ top: scrollTop, behavior: "smooth" });
          }
        }
      }
    },
    [editor]
  );

  // Count items by type
  const counts = useMemo(() => {
    const c = { headings: 0, charts: 0, tables: 0, images: 0 };
    for (const node of tree) {
      if (node.type === "heading") c.headings++;
      else if (node.type === "chart" || node.type === "dynamicBlock") c.charts++;
      else if (node.type === "table" || node.type === "dynamicTable") c.tables++;
      else if (node.type === "image") c.images++;
    }
    return c;
  }, [tree]);

  if (!editor) {
    return (
      <div className={cn("h-full flex items-center justify-center p-4", className)}>
        <p className="text-sm text-muted-foreground">Cargando editor...</p>
      </div>
    );
  }

  return (
    <div className={cn("h-full flex flex-col bg-background border-r", className)}>
      {/* Header */}
      <div className="p-3 border-b">
        <h3 className="text-sm font-semibold mb-2">Estructura</h3>
        <div className="flex flex-wrap gap-1">
          {counts.headings > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {counts.headings} títulos
            </Badge>
          )}
          {counts.charts > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {counts.charts} gráficos
            </Badge>
          )}
          {counts.tables > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {counts.tables} tablas
            </Badge>
          )}
          {counts.images > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {counts.images} imágenes
            </Badge>
          )}
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {tree.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            El documento está vacío
          </p>
        ) : (
          <div className="space-y-0.5">
            {tree.map((node) => (
              <TreeNodeItem
                key={node.id}
                node={node}
                expanded={expanded}
                selectedId={selectedId}
                onToggle={toggleExpanded}
                onClick={handleNodeClick}
                depth={0}
              />
            ))}
          </div>
        )}
      </div>

      {/* Element properties (non-text only) */}
      {selectedElement.type !== "none" && (
        <ElementProperties
          editor={editor}
          element={selectedElement}
        />
      )}
    </div>
  );
}

// ============================================================================
// Tree Node Component
// ============================================================================

interface TreeNodeItemProps {
  node: TreeNode;
  expanded: Set<string>;
  selectedId: string | null;
  onToggle: (id: string) => void;
  onClick: (node: TreeNode) => void;
  depth: number;
}

function TreeNodeItem({
  node,
  expanded,
  selectedId,
  onToggle,
  onClick,
  depth,
}: TreeNodeItemProps) {
  const hasChildren = node.children.length > 0;
  const isExpanded = expanded.has(node.id);
  const isSelected = selectedId === node.id;
  const Icon = getNodeIcon(node.type, node.level);

  return (
    <div>
      <Button
        variant="ghost"
        size="sm"
        className={cn(
          "w-full justify-start h-7 px-1 text-xs font-normal hover:bg-accent",
          isSelected && "bg-accent"
        )}
        style={{ paddingLeft: `${depth * 12 + 4}px` }}
        onClick={() => onClick(node)}
      >
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.id);
            }}
            className="p-0.5 hover:bg-muted rounded"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        ) : (
          <span className="w-4" />
        )}
        <Icon className="h-3.5 w-3.5 ml-1 mr-1.5 shrink-0 text-muted-foreground" />
        <span className="truncate">{node.label}</span>
      </Button>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem
              key={child.id}
              node={child}
              expanded={expanded}
              selectedId={selectedId}
              onToggle={onToggle}
              onClick={onClick}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Element Properties (non-text elements only)
// ============================================================================

function ElementProperties({
  editor,
  element,
}: {
  editor: Editor;
  element: SelectedElement;
}) {
  const handleDelete = () => {
    editor.chain().focus().deleteSelection().run();
  };

  return (
    <div className="border-t">
      <div className="p-3 space-y-3">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          <Palette className="h-3 w-3" />
          Propiedades
        </div>

        {element.type === "chart" && (
          <ChartElementProps attrs={element.attrs} onDelete={handleDelete} />
        )}
        {element.type === "dynamicBlock" && (
          <DynamicBlockElementProps attrs={element.attrs} onDelete={handleDelete} />
        )}
        {element.type === "dynamicTable" && (
          <DynamicTableElementProps attrs={element.attrs} onDelete={handleDelete} />
        )}
        {element.type === "image" && (
          <ImageElementProps attrs={element.attrs} onDelete={handleDelete} />
        )}
      </div>
    </div>
  );
}

function ChartElementProps({
  attrs,
  onDelete,
}: {
  attrs?: Record<string, unknown>;
  onDelete: () => void;
}) {
  const title = (attrs?.title as string) || "Gráfico";
  const chartCode = (attrs?.chartCode as string) || "";

  return (
    <>
      <div className="bg-blue-50 border border-blue-200 rounded-md p-2">
        <p className="text-xs font-medium text-blue-900 truncate">{title}</p>
        {chartCode && (
          <Badge variant="outline" className="mt-1 text-[10px]">
            {chartCode}
          </Badge>
        )}
      </div>
      <div className="flex gap-1.5">
        <Button
          variant="outline"
          size="sm"
          className="flex-1 h-7 text-xs"
          onClick={() => {
            window.dispatchEvent(
              new CustomEvent("edit-chart", { detail: { attrs } })
            );
          }}
        >
          <Pencil className="h-3 w-3 mr-1" />
          Editar
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    </>
  );
}

function DynamicBlockElementProps({
  attrs,
  onDelete,
}: {
  attrs?: Record<string, unknown>;
  onDelete: () => void;
}) {
  const blockType = (attrs?.blockType as string) || "block";
  const config = attrs?.config as { titulo?: string } | undefined;
  const title = config?.titulo || blockType;

  return (
    <>
      <div className="bg-violet-50 border border-violet-200 rounded-md p-2">
        <p className="text-xs font-medium text-violet-900 truncate">{title}</p>
        <Badge variant="outline" className="mt-1 text-[10px]">
          {blockType}
        </Badge>
      </div>
      <p className="text-[10px] text-muted-foreground leading-tight">
        Bloque generado desde plantilla. Datos calculados dinámicamente.
      </p>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-full text-xs text-destructive hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3 w-3 mr-1" />
        Eliminar
      </Button>
    </>
  );
}

function DynamicTableElementProps({
  attrs,
  onDelete,
}: {
  attrs?: Record<string, unknown>;
  onDelete: () => void;
}) {
  const title = (attrs?.title as string) || "Tabla dinámica";

  return (
    <>
      <div className="bg-emerald-50 border border-emerald-200 rounded-md p-2">
        <p className="text-xs font-medium text-emerald-900 truncate">{title}</p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-full text-xs text-destructive hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3 w-3 mr-1" />
        Eliminar
      </Button>
    </>
  );
}

function ImageElementProps({
  attrs,
  onDelete,
}: {
  attrs?: Record<string, unknown>;
  onDelete: () => void;
}) {
  const src = (attrs?.src as string) || "";

  return (
    <>
      {src && (
        <div className="rounded-md border overflow-hidden">
          <img src={src} alt="" className="w-full h-auto max-h-24 object-contain bg-muted" />
        </div>
      )}
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-full text-xs text-destructive hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3 w-3 mr-1" />
        Eliminar
      </Button>
    </>
  );
}
