/**
 * Editor unificado de boletines
 * Editor principal + sección colapsable para template de evento
 */

"use client";

import { useEditor, EditorContent, type JSONContent } from "@tiptap/react";

/**
 * Sanitize TipTap JSON content by removing invalid nodes
 * ProseMirror/TipTap rejects empty text nodes which causes entire content to be dropped
 */
function sanitizeTiptapContent(content: JSONContent): JSONContent {
  if (!content) return content;

  if (typeof content !== "object" || !content.content) {
    return content;
  }

  const sanitizedContent = content.content
    .map((node: JSONContent): JSONContent | null => {
      // Remove empty text nodes (they cause TipTap to reject content)
      if (node.type === "text" && (!node.text || node.text === "")) {
        return null;
      }

      // Recursively sanitize nested content
      if (node.content && Array.isArray(node.content)) {
        return sanitizeTiptapContent(node);
      }

      return node;
    })
    .filter((node): node is JSONContent => node !== null);

  return {
    ...content,
    content: sanitizedContent,
  };
}
import StarterKit from "@tiptap/starter-kit";
import { TextAlign } from "@tiptap/extension-text-align";
import { Underline } from "@tiptap/extension-underline";
import { Placeholder } from "@tiptap/extension-placeholder";
import { useState, useCallback, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  AlignLeft,
  AlignCenter,
  List,
  ListOrdered,
  Undo,
  Redo,
  Heading1,
  Heading2,
  Heading3,
  Type,
  Save,
  Hash,
  Plus,
  BarChart3,
  MapPin,
  Users,
  TrendingUp,
  Activity,
  Bug,
  Calendar,
  Repeat,
  LayoutTemplate,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { useUpdateBoletinTemplate, useUpdateEventSectionTemplate } from "@/features/boletines/api";
import type { BoletinTemplateConfigResponse } from "@/features/boletines/api";
import { DynamicBlockExtension } from "./extensions/dynamic-block-extension";
import { SelectedEventsPlaceholderExtension } from "./extensions/selected-events-placeholder";
import { VariableNodeExtension, VARIABLE_META } from "./extensions/variable-node";
import { EventTemplateProvider, useEventTemplateContext } from "./event-template-context";
import { SelectedBlockProvider } from "./selected-block-context";
import { BlockConfigPanel } from "./block-config-panel";
import { PageBreakExtension } from "../editor/extensions/page-break-extension";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";

interface UnifiedBoletinEditorProps {
  config: BoletinTemplateConfigResponse;
}

// Variables para el editor principal (filtradas por categoría)
const BASE_VARIABLES = Object.entries(VARIABLE_META)
  .filter(([, meta]) => meta.category === "base")
  .map(([key, meta]) => ({ key, ...meta }));

// Variables específicas para el template de evento
const EVENT_VARIABLES = Object.entries(VARIABLE_META)
  .filter(([, meta]) => meta.category === "event")
  .map(([key, meta]) => ({ key, ...meta }));

// ═══════════════════════════════════════════════════════════════════════════════
// BLOQUES DINÁMICOS - Organizados por propósito claro
// ═══════════════════════════════════════════════════════════════════════════════

interface BlockDefinition {
  queryType: string;
  /** Unique block type identifier for config panel */
  blockType: string;
  title: string;
  description: string;
  icon: typeof BarChart3;
  category: "resumen" | "evento" | "comparacion" | "distribucion";
  renderType: "table" | "chart";
  defaultParams: Record<string, unknown>;
  defaultConfig: Record<string, unknown>;
  badge?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// BLOQUES PARA ESTRUCTURA BASE (editor principal)
// Estos bloques van FUERA del loop de eventos - requieren especificar qué datos mostrar
// ═══════════════════════════════════════════════════════════════════════════════
const MAIN_BLOCKS: BlockDefinition[] = [
  // ─────────────────────────────────────────────────────────────────────────────
  // RESUMEN GENERAL
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "top_enos",
    blockType: "top_enos",
    title: "Top Eventos del Período",
    description: "Ranking de eventos más notificados",
    icon: BarChart3,
    category: "resumen",
    renderType: "table",
    defaultParams: { limit: 10 },
    defaultConfig: { titulo: "Eventos de Notificación Obligatoria - SE {{ semana_epidemiologica_inicio }} a {{ semana_epidemiologica_actual }}" },
    badge: "Tabla",
  },
  {
    queryType: "comparacion_periodos",
    blockType: "comparacion_periodos_global",
    title: "Comparación de Períodos",
    description: "Todos los eventos: período actual vs anterior",
    icon: TrendingUp,
    category: "comparacion",
    renderType: "table",
    defaultParams: { limit: 10 },
    defaultConfig: { titulo: "Comparación con Período Anterior" },
    badge: "Tabla",
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // CURVAS DE EVENTO ESPECÍFICO (fuera del loop)
  // Requieren seleccionar qué evento(s) mostrar
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "curva_epidemiologica",
    blockType: "curva_evento_especifico",
    title: "Curva de Evento",
    description: "Casos por semana de UN evento específico",
    icon: Activity,
    category: "evento",
    renderType: "chart",
    defaultParams: {},
    defaultConfig: { titulo: "Casos por Semana Epidemiológica", height: 350, chart_type: "bar" },
    badge: "Requiere evento",
  },
  {
    queryType: "corredor_endemico_chart",
    blockType: "corredor_evento_especifico",
    title: "Corredor de Evento",
    description: "Corredor endémico de UN evento específico",
    icon: TrendingUp,
    category: "evento",
    renderType: "chart",
    defaultParams: { periodo: "anual" },
    defaultConfig: { titulo: "Corredor Endémico", height: 400 },
    badge: "Requiere evento",
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // COMPARACIONES MULTI-EVENTO
  // Comparan varios eventos en el mismo gráfico
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "curva_epidemiologica",
    blockType: "curva_comparar_eventos",
    title: "Comparar Eventos (Curva)",
    description: "Curvas de múltiples eventos superpuestas",
    icon: Activity,
    category: "comparacion",
    renderType: "chart",
    defaultParams: { agrupar_por: "evento" },
    defaultConfig: { titulo: "Comparación de Eventos por Semana", height: 350, chart_type: "line", show_legend: true },
    badge: "Multi-evento",
  },
  {
    queryType: "distribucion_edad",
    blockType: "edad_comparar_eventos",
    title: "Comparar Eventos (Edad)",
    description: "Distribución por edad de múltiples eventos",
    icon: Users,
    category: "comparacion",
    renderType: "chart",
    defaultParams: { agrupar_por: "evento" },
    defaultConfig: { titulo: "Distribución por Edad - Comparación", height: 350, chart_type: "stacked_bar", show_legend: true },
    badge: "Multi-evento",
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // ANÁLISIS POR AGENTE
  // Muestran distribución de agentes para evento(s) específico(s)
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "distribucion_agentes",
    blockType: "distribucion_agentes",
    title: "Agentes Detectados",
    description: "Total de detecciones por agente etiológico",
    icon: Bug,
    category: "distribucion",
    renderType: "chart",
    defaultParams: { resultado: "positivo" },
    defaultConfig: { titulo: "Agentes Etiológicos Detectados", height: 350, chart_type: "bar" },
    badge: "Requiere config",
  },
  {
    queryType: "curva_epidemiologica",
    blockType: "curva_por_agente",
    title: "Evolución por Agente",
    description: "Casos por semana separados por agente",
    icon: Activity,
    category: "distribucion",
    renderType: "chart",
    defaultParams: { agrupar_por: "agente", resultado: "positivo" },
    defaultConfig: { titulo: "Evolución por Agente", height: 400, chart_type: "stacked_bar", show_legend: true },
    badge: "Requiere config",
  },
  {
    queryType: "distribucion_edad",
    blockType: "edad_por_agente",
    title: "Edad por Agente",
    description: "Distribución etaria separada por agente",
    icon: Users,
    category: "distribucion",
    renderType: "chart",
    defaultParams: { agrupar_por: "agente", resultado: "positivo" },
    defaultConfig: { titulo: "Distribución por Edad y Agente", height: 400, chart_type: "stacked_bar", show_legend: true },
    badge: "Requiere config",
  },
];

// ═══════════════════════════════════════════════════════════════════════════════
// BLOQUES PARA TEMPLATE DE EVENTO (dentro del loop)
// Estos bloques usan automáticamente el evento del contexto del loop
// ═══════════════════════════════════════════════════════════════════════════════
const EVENT_BLOCKS: BlockDefinition[] = [
  // ─────────────────────────────────────────────────────────────────────────────
  // GRÁFICOS DEL EVENTO (usan {{ evento_codigo }} automáticamente)
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "corredor_endemico_chart",
    blockType: "corredor_loop",
    title: "Corredor Endémico",
    description: "Gráfico anual con zonas epidémicas del evento",
    icon: TrendingUp,
    category: "evento",
    renderType: "chart",
    defaultParams: { periodo: "anual" },
    defaultConfig: { titulo: "Corredor Endémico {{ nombre_evento_sanitario }} - {{ anio_epidemiologico }}", height: 400 },
    badge: "Automático",
  },
  {
    queryType: "curva_epidemiologica",
    blockType: "curva_loop",
    title: "Curva Epidemiológica",
    description: "Casos por semana del evento",
    icon: Activity,
    category: "evento",
    renderType: "chart",
    defaultParams: {},
    defaultConfig: { titulo: "Casos por Semana - {{ nombre_evento_sanitario }}", height: 350, chart_type: "bar" },
    badge: "Automático",
  },
  {
    queryType: "distribucion_edad",
    blockType: "edad_loop",
    title: "Distribución por Edad",
    description: "Casos por grupo etario del evento",
    icon: Users,
    category: "evento",
    renderType: "chart",
    defaultParams: {},
    defaultConfig: { titulo: "Distribución por Edad - {{ nombre_evento_sanitario }}", height: 350, chart_type: "bar" },
    badge: "Automático",
  },
  {
    queryType: "distribucion_geografica",
    blockType: "mapa_loop",
    title: "Mapa de Casos",
    description: "Distribución geográfica del evento",
    icon: MapPin,
    category: "evento",
    renderType: "chart",
    defaultParams: {},
    defaultConfig: { titulo: "Distribución Geográfica - {{ nombre_evento_sanitario }}", height: 400 },
    badge: "Automático",
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // COMPARACIONES (dentro del loop, compara el evento actual)
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "comparacion_anual",
    blockType: "comparacion_anual_loop",
    title: "Comparación Interanual",
    description: "Año actual vs año anterior del evento",
    icon: Calendar,
    category: "comparacion",
    renderType: "chart",
    defaultParams: { comparar_con: "anio_anterior", acumulado: true },
    defaultConfig: { titulo: "{{ nombre_evento_sanitario }} - {{ anio_epidemiologico }} vs Año Anterior", height: 350 },
    badge: "Automático",
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // DESGLOSE POR AGENTE (dentro del loop, para el evento actual)
  // ─────────────────────────────────────────────────────────────────────────────
  {
    queryType: "distribucion_agentes",
    blockType: "agentes_loop",
    title: "Agentes del Evento",
    description: "Detecciones por agente para este evento",
    icon: Bug,
    category: "distribucion",
    renderType: "chart",
    defaultParams: { resultado: "positivo" },
    defaultConfig: { titulo: "Agentes Detectados - {{ nombre_evento_sanitario }}", height: 350, chart_type: "bar" },
    badge: "Configurable",
  },
  {
    queryType: "distribucion_edad",
    blockType: "edad_por_agente_loop",
    title: "Edad por Agente",
    description: "Distribución etaria separada por agente",
    icon: Users,
    category: "distribucion",
    renderType: "chart",
    defaultParams: { agrupar_por: "agente", resultado: "positivo" },
    defaultConfig: { titulo: "Distribución por Edad y Agente - {{ nombre_evento_sanitario }}", height: 400, chart_type: "stacked_bar", show_legend: true },
    badge: "Configurable",
  },
];

export function UnifiedBoletinEditor({ config }: UnifiedBoletinEditorProps) {
  return (
    <EventTemplateProvider>
      <SelectedBlockProvider>
        <UnifiedBoletinEditorInner config={config} />
      </SelectedBlockProvider>
    </EventTemplateProvider>
  );
}

function UnifiedBoletinEditorInner({ config }: UnifiedBoletinEditorProps) {
  const [hasChanges, setHasChanges] = useState(false);
  const isInitializingRef = useRef(true);
  const updateBaseMutation = useUpdateBoletinTemplate();
  const updateEventMutation = useUpdateEventSectionTemplate();
  const { setEventTemplateContent } = useEventTemplateContext();

  // Track changes only after initialization is complete
  // Using ref to avoid stale closure in useEditor's onUpdate
  const markChanged = useCallback(() => {
    if (!isInitializingRef.current) {
      setHasChanges(true);
    }
  }, []);

  // Build initial content for main editor
  const buildBaseContent = useCallback((): JSONContent => {
    const staticContent = config.static_content_template as JSONContent | null;
    if (staticContent) {
      // Sanitize content to remove empty text nodes
      return sanitizeTiptapContent(staticContent);
    }
    return { type: "doc", content: [] };
  }, [config]);

  // Build initial content for event template editor
  const buildEventContent = useCallback((): JSONContent => {
    const eventContent = config.event_section_template as JSONContent | null;

    if (eventContent?.content) {
      return sanitizeTiptapContent(eventContent);
    }
    // Default event template
    return {
      type: "doc",
      content: [
        {
          type: "heading",
          attrs: { level: 3 },
          content: [{ type: "text", text: "{{ tipo_evento }}" }]
        },
        {
          type: "paragraph",
          content: [{ type: "text", text: "{{ tendencia_texto }}" }]
        }
      ]
    };
  }, [config]);

  // Event template editor extensions
  const eventEditorExtensions = useMemo(() => [
    StarterKit.configure({ heading: { levels: [2, 3, 4] } }),
    Underline.configure({}),
    TextAlign.configure({
      types: ["heading", "paragraph"],
      alignments: ["left", "center", "right"],
    }),
    PageBreakExtension.configure({}),
    DynamicBlockExtension.configure({ isInEventLoop: true }),
    VariableNodeExtension.configure({}),
    Placeholder.configure({
      placeholder: "Diseña cómo se mostrará cada evento seleccionado...",
    }),
  ], []);

  const eventEditor = useEditor({
    immediatelyRender: false,
    extensions: eventEditorExtensions,
    content: { type: "doc", content: [] },
    editorProps: {
      attributes: {
        class:
          "min-h-[500px] p-6 outline-none prose prose-sm max-w-none focus:outline-none " +
          "[&_h2]:text-xl [&_h2]:font-bold [&_h2]:mb-3 [&_h2]:mt-5 " +
          "[&_h3]:text-lg [&_h3]:font-semibold [&_h3]:mb-2 [&_h3]:mt-4 " +
          "[&_h4]:text-base [&_h4]:font-medium [&_h4]:mb-1 " +
          "[&_p]:text-sm [&_p]:mb-2 " +
          "[&_ul]:mb-3 [&_ul]:ml-4 [&_ol]:mb-3 [&_ol]:ml-4 [&_li]:mb-1",
      },
    },
    onUpdate: ({ editor }) => {
      markChanged();
      setEventTemplateContent(editor.getJSON());
    },
    onCreate: ({ editor }) => {
      // Load content in onCreate when schema is fully ready
      const eventContent = buildEventContent();
      editor.commands.setContent(eventContent);
      // Mark all existing blocks as being in the event loop
      editor.commands.markBlocksAsEventLoop();
      setEventTemplateContent(editor.getJSON());
    },
  });

  // Main editor extensions
  const mainEditorExtensions = useMemo(() => [
    StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
    Underline.configure({}),
    TextAlign.configure({
      types: ["heading", "paragraph"],
      alignments: ["left", "center", "right"],
    }),
    PageBreakExtension.configure({}),
    DynamicBlockExtension.configure({}),
    SelectedEventsPlaceholderExtension.configure({}),
    VariableNodeExtension.configure({}),
    Placeholder.configure({
      placeholder: "Escribe el contenido del boletín...",
    }),
  ], []);

  const mainEditor = useEditor({
    immediatelyRender: false,
    extensions: mainEditorExtensions,
    content: { type: "doc", content: [] },
    editorProps: {
      attributes: {
        class:
          "min-h-[500px] p-6 outline-none prose prose-sm max-w-none focus:outline-none " +
          "[&_h1]:text-2xl [&_h1]:font-bold [&_h1]:mb-4 [&_h1]:mt-6 " +
          "[&_h2]:text-xl [&_h2]:font-bold [&_h2]:mb-3 [&_h2]:mt-5 " +
          "[&_h3]:text-lg [&_h3]:font-semibold [&_h3]:mb-2 [&_h3]:mt-4 " +
          "[&_p]:text-sm [&_p]:leading-6 [&_p]:mb-3 " +
          "[&_ul]:mb-3 [&_ul]:ml-4 [&_ol]:mb-3 [&_ol]:ml-4 [&_li]:mb-1",
      },
    },
    onUpdate: markChanged,
    onCreate: ({ editor }) => {
      const baseContent = buildBaseContent();
      editor.commands.setContent(baseContent);

      // Mark initialization complete after both editors are ready
      setTimeout(() => {
        isInitializingRef.current = false;
      }, 0);
    },
  });

  // Content is now loaded in onCreate callbacks - no need for useEffect initialization

  // Save both templates
  const handleSave = async () => {
    if (!mainEditor || !eventEditor) return;

    try {
      await Promise.all([
        updateBaseMutation.mutateAsync({ body: { content: mainEditor.getJSON() } }),
        updateEventMutation.mutateAsync({ body: { content: eventEditor.getJSON() } }),
      ]);
      toast.success("Plantilla guardada correctamente");
      setHasChanges(false);
    } catch {
      toast.error("Error al guardar la plantilla");
    }
  };

  const handleReset = () => {
    mainEditor?.commands.setContent(buildBaseContent());
    eventEditor?.commands.setContent(buildEventContent());
    setHasChanges(false);
  };

  const isPending = updateBaseMutation.isPending || updateEventMutation.isPending;

  if (!mainEditor || !eventEditor) return null;

  // Toolbar component reutilizable
  const EditorToolbar = ({ editor, variables, blocks, isEventEditor = false }: {
    editor: typeof mainEditor;
    variables: typeof BASE_VARIABLES;
    blocks: typeof MAIN_BLOCKS | typeof EVENT_BLOCKS;
    isEventEditor?: boolean;
  }) => (
    <div className="flex flex-wrap items-center gap-1 p-2 bg-muted/30 rounded-md border">
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()}>
        <Undo className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()}>
        <Redo className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="h-8">
            <Type className="h-4 w-4 mr-1" />
            {editor.isActive("heading", { level: 1 }) ? "H1" :
             editor.isActive("heading", { level: 2 }) ? "H2" :
             editor.isActive("heading", { level: 3 }) ? "H3" : "P"}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => editor.chain().focus().setParagraph().run()}>Párrafo</DropdownMenuItem>
          {!isEventEditor && <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}><Heading1 className="h-4 w-4 mr-2" /> Título H1</DropdownMenuItem>}
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}><Heading2 className="h-4 w-4 mr-2" /> Título H2</DropdownMenuItem>
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}><Heading3 className="h-4 w-4 mr-2" /> Título H3</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Separator orientation="vertical" className="h-6 mx-1" />

      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive("bold") ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().toggleBold().run()}>
        <Bold className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive("italic") ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().toggleItalic().run()}>
        <Italic className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive("underline") ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().toggleUnderline().run()}>
        <UnderlineIcon className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive("bulletList") ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().toggleBulletList().run()}>
        <List className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive("orderedList") ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().toggleOrderedList().run()}>
        <ListOrdered className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive({ textAlign: "left" }) ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().setTextAlign("left").run()}>
        <AlignLeft className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="icon" className={`h-8 w-8 ${editor.isActive({ textAlign: "center" }) ? "bg-muted" : ""}`} onClick={() => editor.chain().focus().setTextAlign("center").run()}>
        <AlignCenter className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Variables dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <Hash className="h-4 w-4 mr-1" /> Variables
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="max-h-[300px] overflow-y-auto">
          <DropdownMenuLabel className="text-xs">{isEventEditor ? "Variables de evento" : "Variables generales"}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {variables.map((v) => {
            const Icon = v.icon;
            return (
              <DropdownMenuItem key={v.key} onClick={() => editor.chain().focus().insertVariable(v.key).run()} className="flex justify-between">
                <span className="flex items-center gap-2"><Icon className="h-4 w-4" />{v.label}</span>
                <Badge variant="secondary" className={`text-[10px] ml-4 ${isEventEditor ? "bg-violet-100 text-violet-700" : ""}`}>{v.example}</Badge>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Blocks dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="h-8">
            <Plus className="h-4 w-4 mr-1" /> Insertar Bloque
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-80 max-h-[400px] overflow-y-auto">
          {isEventEditor ? (
            <>
              {/* Event blocks - organized by category */}
              <DropdownMenuLabel className="text-xs text-emerald-600 font-medium">Gráficos del Evento</DropdownMenuLabel>
              {(blocks as typeof EVENT_BLOCKS).filter(b => b.category === "evento").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig,
                      isInEventLoop: true,
                    }).run()}
                    className="flex items-start gap-2 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-emerald-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[9px] px-1 py-0 bg-emerald-100 text-emerald-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs text-indigo-600 font-medium">Comparaciones</DropdownMenuLabel>
              {(blocks as typeof EVENT_BLOCKS).filter(b => b.category === "comparacion").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig,
                      isInEventLoop: true,
                    }).run()}
                    className="flex items-start gap-2 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-indigo-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[9px] px-1 py-0 bg-indigo-100 text-indigo-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs text-amber-600 font-medium">Desglose por Agente</DropdownMenuLabel>
              {(blocks as typeof EVENT_BLOCKS).filter(b => b.category === "distribucion").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig,
                      isInEventLoop: true,
                    }).run()}
                    className="flex items-start gap-2 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-amber-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[9px] px-1 py-0 bg-amber-100 text-amber-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
            </>
          ) : (
            <>
              {/* Main blocks - organized by category */}
              <DropdownMenuLabel className="text-xs text-blue-600 font-medium">Resumen General</DropdownMenuLabel>
              {(blocks as typeof MAIN_BLOCKS).filter(b => b.category === "resumen").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig
                    }).run()}
                    className="flex items-start gap-3 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-blue-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-blue-100 text-blue-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs text-emerald-600 font-medium">Evento Específico</DropdownMenuLabel>
              {(blocks as typeof MAIN_BLOCKS).filter(b => b.category === "evento").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig
                    }).run()}
                    className="flex items-start gap-3 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-emerald-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-emerald-100 text-emerald-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs text-indigo-600 font-medium">Comparaciones Multi-Evento</DropdownMenuLabel>
              {(blocks as typeof MAIN_BLOCKS).filter(b => b.category === "comparacion").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig
                    }).run()}
                    className="flex items-start gap-3 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-indigo-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-indigo-100 text-indigo-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs text-amber-600 font-medium">Análisis por Agente</DropdownMenuLabel>
              {(blocks as typeof MAIN_BLOCKS).filter(b => b.category === "distribucion").map((block) => {
                const Icon = block.icon;
                return (
                  <DropdownMenuItem
                    key={block.blockType}
                    onClick={() => editor.chain().focus().insertDynamicBlock({
                      blockId: `${block.blockType}_${Date.now()}`,
                      blockType: block.blockType,
                      queryType: block.queryType,
                      renderType: block.renderType,
                      queryParams: block.defaultParams,
                      config: block.defaultConfig
                    }).run()}
                    className="flex items-start gap-3 py-2"
                  >
                    <Icon className="h-4 w-4 mt-0.5 shrink-0 text-amber-600" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{block.title}</span>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-amber-100 text-amber-700">{block.badge}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground truncate">{block.description}</div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Special buttons */}
      {!isEventEditor && (
        <Button variant="default" size="sm" className="h-8 bg-violet-600 hover:bg-violet-700" onClick={() => editor.chain().focus().insertSelectedEventsPlaceholder().run()}>
          <Repeat className="h-4 w-4 mr-1" /> Loop de Eventos
        </Button>
      )}

      {/* Save button - only in main editor toolbar */}
      {!isEventEditor && (
        <>
          <div className="flex-1" />
          {hasChanges && (
            <Button variant="outline" size="sm" className="h-8" onClick={handleReset} disabled={isPending}>
              Descartar
            </Button>
          )}
          <Button onClick={handleSave} disabled={!hasChanges || isPending} size="sm" className="h-8">
            <Save className="h-4 w-4 mr-1" />
            {isPending ? "Guardando..." : "Guardar"}
          </Button>
        </>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-full relative">
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* ════════════════════════════════════════════════════════════════════ */}
        {/* LEFT: EDITORS */}
        {/* ════════════════════════════════════════════════════════════════════ */}
        <ResizablePanel defaultSize={72} minSize={50}>
          <div className="h-full overflow-auto p-4">
            <div className="space-y-6">
              {/* EDITOR 1: ESTRUCTURA BASE */}
              <div className="flex flex-col gap-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-2.5">
                  <div className="flex items-center gap-2">
                    <LayoutTemplate className="h-4 w-4 text-blue-600 shrink-0" />
                    <p className="text-sm font-medium text-blue-900">Estructura base</p>
                    <span className="text-xs text-blue-600">
                      — Usa <strong>&quot;Loop de Eventos&quot;</strong> para indicar dónde se repiten
                    </span>
                  </div>
                </div>

                <EditorToolbar editor={mainEditor} variables={BASE_VARIABLES} blocks={MAIN_BLOCKS} />

                <div className="min-h-[300px] border rounded-md bg-white overflow-auto">
                  <EditorContent editor={mainEditor} />
                </div>
              </div>

              {/* EDITOR 2: TEMPLATE POR EVENTO */}
              <div className="flex flex-col gap-3">
                <div className="bg-violet-50 border border-violet-200 rounded-lg p-2.5">
                  <div className="flex items-center gap-2">
                    <Repeat className="h-4 w-4 text-violet-600 shrink-0" />
                    <p className="text-sm font-medium text-violet-900">Template por evento</p>
                    <span className="text-xs text-violet-600">
                      — Se genera una vez por cada evento seleccionado
                    </span>
                  </div>
                </div>

                <EditorToolbar editor={eventEditor} variables={EVENT_VARIABLES} blocks={EVENT_BLOCKS} isEventEditor />

                <div className="min-h-[300px] border border-violet-200 rounded-md bg-white overflow-auto">
                  <EditorContent editor={eventEditor} />
                </div>
              </div>
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* ════════════════════════════════════════════════════════════════════ */}
        {/* RIGHT: BLOCK CONFIG PANEL */}
        {/* ════════════════════════════════════════════════════════════════════ */}
        <ResizablePanel defaultSize={28} minSize={22} maxSize={40} className="min-w-0">
          <BlockConfigPanel />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
