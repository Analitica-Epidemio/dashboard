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

import { DynamicTableExtension } from "./extensions/DynamicTableExtension";
import { DynamicChartExtension } from "./extensions/DynamicChartExtension";
import { PageBreakExtension } from "./extensions/PageBreakExtension";
import { VariableExtension } from "./extensions/VariableExtension";
import { BoletinMenuBar } from "./BoletinMenuBar";

interface BoletinTiptapEditorProps {
  initialHtml?: string;
  onChange?: (html: string) => void;
  className?: string;
}

// Extensión de Table con estilos minimalistas tipo Google Docs
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
        default:
          "border border-gray-300 px-3 py-2 text-[11pt] text-gray-900",
      },
    };
  },
});

const CustomTableHeader = TableHeader.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: {
        default:
          "border border-gray-300 px-3 py-2 bg-gray-100 font-semibold text-[11pt] text-gray-900",
      },
    };
  },
});

export function BoletinTiptapEditor({
  initialHtml,
  onChange,
  className = "",
}: BoletinTiptapEditorProps) {
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
        placeholder: "Comienza a escribir tu boletin aqui...",
      }),
      // Nuevas extensiones para contenido dinamico
      DynamicTableExtension,
      DynamicChartExtension,
      PageBreakExtension,
      VariableExtension,
    ],
    content: initialHtml || "",
    editorProps: {
      attributes: {
        class:
          "min-h-[297mm] outline-none prose prose-base max-w-none focus:outline-none " +
          // Estilo Google Docs - Headings limpios
          "[&_h1]:text-3xl [&_h1]:font-normal [&_h1]:mb-3 [&_h1]:mt-6 [&_h1]:text-gray-900 " +
          "[&_h2]:text-2xl [&_h2]:font-normal [&_h2]:mb-2 [&_h2]:mt-5 [&_h2]:text-gray-900 " +
          "[&_h3]:text-xl [&_h3]:font-normal [&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-gray-900 " +
          // Párrafos - estilo Google Docs limpio
          "[&_p]:text-[11pt] [&_p]:leading-[1.15] [&_p]:mb-[11pt] [&_p]:text-gray-900 " +
          // Listas - estilo Google Docs con bullets visibles
          "[&_ul]:list-disc [&_ul]:mb-[11pt] [&_ul]:ml-6 [&_ul]:pl-0 " +
          "[&_ol]:list-decimal [&_ol]:mb-[11pt] [&_ol]:ml-6 [&_ol]:pl-0 " +
          "[&_li]:text-[11pt] [&_li]:leading-[1.15] [&_li]:text-gray-900 [&_li]:mb-0 " +
          // Blockquotes - minimalista
          "[&_blockquote]:border-l-4 [&_blockquote]:border-gray-300 [&_blockquote]:pl-4 " +
          "[&_blockquote]:my-[11pt] [&_blockquote]:text-[11pt] [&_blockquote]:text-gray-700 [&_blockquote]:italic " +
          // Tablas - estilo limpio
          "[&_table]:border-collapse [&_table]:w-full [&_table]:my-4 " +
          "[&_td]:border [&_td]:border-gray-300 [&_td]:px-3 [&_td]:py-2 [&_td]:text-[11pt] [&_td]:text-gray-900 " +
          "[&_th]:border [&_th]:border-gray-300 [&_th]:px-3 [&_th]:py-2 [&_th]:bg-gray-100 [&_th]:font-semibold [&_th]:text-[11pt] [&_th]:text-gray-900 " +
          // Imágenes
          "[&_img]:max-w-full [&_img]:h-auto [&_img]:my-4 " +
          // Strong y énfasis
          "[&_strong]:font-semibold [&_strong]:text-gray-900 " +
          "[&_em]:italic [&_em]:text-gray-900",
      },
      // Manejo de archivos arrastrados (imagenes)
      handleDrop: (view, event, _slice, moved) => {
        if (
          !moved &&
          event.dataTransfer &&
          event.dataTransfer.files &&
          event.dataTransfer.files[0]
        ) {
          const file = event.dataTransfer.files[0];
          const fileType = file.type;

          if (fileType.startsWith("image/")) {
            event.preventDefault();

            const reader = new FileReader();
            reader.onload = (e) => {
              const src = e.target?.result as string;
              const { schema } = view.state;
              const coordinates = view.posAtCoords({
                left: event.clientX,
                top: event.clientY,
              });

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
      // Manejo de pegar imagenes desde el portapapeles
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
      // Solo actualizar si el contenido es diferente
      if (currentContent !== initialHtml) {
        editor.commands.setContent(initialHtml);
      }
    }
  }, [editor, initialHtml]);

  if (!editor) {
    return null;
  }

  return (
    <div className={`relative bg-[#f9fbfd] ${className}`}>
      {/* MenuBar - sticky en la parte superior */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <BoletinMenuBar editor={editor} />
      </div>

      {/* Editor - estilo Google Docs continuo */}
      <div className="flex justify-center pt-6 pb-16 px-4">
        <div
          className="bg-white shadow-md relative"
          style={{
            width: '210mm',
            minHeight: '297mm',
            padding: '2.54cm', // Márgenes estándar A4 (1 inch)
          }}
        >
          {/* Contenido del editor */}
          <EditorContent editor={editor} />
        </div>
      </div>
    </div>
  );
}
