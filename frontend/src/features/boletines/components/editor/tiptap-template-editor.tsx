"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableCell } from "@tiptap/extension-table-cell";
import { TableHeader } from "@tiptap/extension-table-header";
import { Image } from "@tiptap/extension-image";
import { TextAlign } from "@tiptap/extension-text-align";
import { Underline } from "@tiptap/extension-underline";
import { Placeholder } from "@tiptap/extension-placeholder";
import { useEffect } from "react";

import { VariableExtension } from "./extensions/variable-extension";
import { MenuBar } from "./menu-bar";

interface TiptapTemplateEditorProps {
  initialHtml?: string;
  onChange?: (html: string) => void;
  className?: string;
}

// Lista de variables conocidas con sus labels, emojis y tipos
const VARIABLE_INFO: Record<string, { label: string; emoji: string; type: "basic" | "stat" | "chart" }> = {
  disease_name: { label: "Nombre de Enfermedad", emoji: "🦠", type: "basic" },
  date_from: { label: "Fecha Desde", emoji: "📅", type: "basic" },
  date_to: { label: "Fecha Hasta", emoji: "🗓️", type: "basic" },
  generated_date: { label: "Fecha de Generación", emoji: "📆", type: "basic" },
  total_cases: { label: "Total de Casos", emoji: "📊", type: "stat" },
  confirmed: { label: "Casos Confirmados", emoji: "✅", type: "stat" },
  suspected: { label: "Casos Sospechosos", emoji: "🔍", type: "stat" },
  discarded: { label: "Casos Descartados", emoji: "❌", type: "stat" },
  deaths: { label: "Fallecidos", emoji: "💔", type: "stat" },
  active_cases: { label: "Casos Activos", emoji: "🏥", type: "stat" },
  recovered: { label: "Recuperados", emoji: "💚", type: "stat" },
  chart_temporal: { label: "GRÁFICO: Evolución Temporal", emoji: "📈", type: "chart" },
  chart_geographic: { label: "GRÁFICO: Distribución Geográfica", emoji: "🗺️", type: "chart" },
  chart_age_distribution: { label: "GRÁFICO: Distribución por Edad", emoji: "👥", type: "chart" },
  chart_gender_distribution: { label: "GRÁFICO: Distribución por Sexo", emoji: "⚧️", type: "chart" },
};

// Función para convertir variables de texto plano {{var}} a nodos HTML parseables
function preprocessHtmlVariables(html: string): string {
  if (!html) return html;

  // Reemplazar {{variable_name}} con <span data-variable="variable_name">{{variable_name}}</span>
  return html.replace(/\{\{(\w+)\}\}/g, (match, variableKey) => {
    const info = VARIABLE_INFO[variableKey] || { label: variableKey, emoji: "📊", type: "basic" as const };
    return `<span data-variable="${variableKey}" class="variable-placeholder" data-label="${info.label}" data-emoji="${info.emoji}" data-type="${info.type}">${match}</span>`;
  });
}

// Extensión de Table con estilos personalizados
const CustomTable = Table.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: {
        default: "border-collapse w-full my-4",
      },
    };
  },
});

const CustomTableCell = TableCell.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: {
        default: "border border-gray-300 px-4 py-2",
      },
    };
  },
});

const CustomTableHeader = TableHeader.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: {
        default: "border border-gray-300 px-4 py-2 bg-gray-100 font-semibold",
      },
    };
  },
});

export function TiptapTemplateEditor({
  initialHtml,
  onChange,
  className = "",
}: TiptapTemplateEditorProps) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Underline,
      TextAlign.configure({
        types: ["heading", "paragraph"],
        alignments: ["left", "center", "right", "justify"],
      }),
      CustomTable.configure({
        resizable: false,
        HTMLAttributes: {
          class: "border-collapse w-full my-4",
        },
      }),
      TableRow,
      CustomTableCell,
      CustomTableHeader,
      Image.configure({
        inline: true,
        allowBase64: true,
        HTMLAttributes: {
          class: "max-w-full h-auto my-4 rounded-lg shadow-sm",
        },
      }),
      Placeholder.configure({
        placeholder: "Comienza a escribir tu template aquí...",
      }),
      VariableExtension,
    ],
    content: preprocessHtmlVariables(initialHtml || ""),
    editorProps: {
      attributes: {
        class:
          "min-h-[800px] px-12 py-8 outline-none prose prose-base max-w-none focus:outline-none " +
          "[&_h1]:text-4xl [&_h1]:font-bold [&_h1]:mb-6 [&_h1]:mt-8 " +
          "[&_h2]:text-3xl [&_h2]:font-bold [&_h2]:mb-4 [&_h2]:mt-6 " +
          "[&_h3]:text-2xl [&_h3]:font-semibold [&_h3]:mb-3 [&_h3]:mt-5 " +
          "[&_p]:text-base [&_p]:leading-7 [&_p]:mb-4 " +
          "[&_ul]:mb-4 [&_ul]:ml-6 [&_ol]:mb-4 [&_ol]:ml-6 [&_li]:mb-2 " +
          "[&_blockquote]:border-l-4 [&_blockquote]:border-border [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:my-4 " +
          "[&_table]:border-collapse [&_table]:w-full [&_table]:my-4 " +
          "[&_td]:border [&_td]:border-gray-300 [&_td]:px-4 [&_td]:py-2 " +
          "[&_th]:border [&_th]:border-gray-300 [&_th]:px-4 [&_th]:py-2 [&_th]:bg-gray-100 [&_th]:font-semibold " +
          "[&_img]:max-w-full [&_img]:h-auto [&_img]:my-4 [&_img]:rounded-lg [&_img]:shadow-sm",
      },
      // Manejo de archivos arrastrados (imágenes)
      handleDrop: (view, event, _slice, moved) => {
        if (!moved && event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0]) {
          const file = event.dataTransfer.files[0];
          const fileType = file.type;

          if (fileType.startsWith("image/")) {
            event.preventDefault();

            const reader = new FileReader();
            reader.onload = (e) => {
              const src = e.target?.result as string;
              const { schema } = view.state;
              const coordinates = view.posAtCoords({ left: event.clientX, top: event.clientY });

              if (coordinates) {
                const node = schema.nodes.image.create({ src });
                const transaction = view.state.tr.insert(coordinates.pos, node);
                view.dispatch(transaction);
              }
            };
            reader.readAsDataURL(file);
            return true;
          }
        }
        return false;
      },
      // Manejo de pegar imágenes desde el portapapeles
      handlePaste: (view, event) => {
        const items = event.clipboardData?.items;
        if (!items) return false;

        for (let i = 0; i < items.length; i++) {
          if (items[i].type.startsWith("image/")) {
            event.preventDefault();

            const file = items[i].getAsFile();
            if (file) {
              const reader = new FileReader();
              reader.onload = (e) => {
                const src = e.target?.result as string;
                editor?.chain().focus().setImage({ src }).run();
              };
              reader.readAsDataURL(file);
              return true;
            }
          }
        }
        return false;
      },
    },
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      onChange?.(html);
    },
  });

  // Actualizar contenido cuando cambia initialHtml
  useEffect(() => {
    if (editor && initialHtml !== undefined) {
      const currentContent = editor.getHTML();
      const processedHtml = preprocessHtmlVariables(initialHtml);
      // Solo actualizar si el contenido es diferente
      if (currentContent !== processedHtml) {
        editor.commands.setContent(processedHtml);
      }
    }
  }, [editor, initialHtml]);

  if (!editor) {
    return null;
  }

  return (
    <div className={`relative bg-background ${className}`}>
      {/* MenuBar - sticky en la parte superior */}
      <div className="sticky top-0 z-10 bg-background border-b">
        <MenuBar editor={editor} />
      </div>

      {/* Editor - aspecto de documento */}
      <div className="relative">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
