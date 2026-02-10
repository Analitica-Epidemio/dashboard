"use client";

import { useMemo } from "react";
import { useEditor, EditorContent, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableCell } from "@tiptap/extension-table-cell";
import { TableHeader } from "@tiptap/extension-table-header";
import { Image } from "@tiptap/extension-image";
import { TextAlign } from "@tiptap/extension-text-align";
import { Underline } from "@tiptap/extension-underline";
import { DynamicTableExtension } from "@/features/boletines/components/editor/extensions/dynamic-table-extension";
import { DynamicChartExtension } from "@/features/boletines/components/editor/extensions/dynamic-chart-extension";
import { PageBreakExtension } from "@/features/boletines/components/editor/extensions/page-break-extension";
import { VariableNodeExtension } from "@/features/boletines/components/config/extensions/variable-node";
import { DynamicBlockExtension } from "@/features/boletines/components/config/extensions/dynamic-block-extension";
import { SelectedEventsPlaceholderExtension } from "@/features/boletines/components/config/extensions/selected-events-placeholder";

function parseContent(content: string | undefined): string | JSONContent {
  if (!content) return "";
  const trimmed = content.trim();
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed && typeof parsed === "object" && parsed.type === "doc") {
        return parsed as JSONContent;
      }
    } catch {
      // Not valid JSON, treat as HTML
    }
  }
  return content;
}

const CustomTable = Table.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: { default: "border-collapse w-full my-4" },
    };
  },
});

const CustomTableCell = TableCell.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: { default: "border border-gray-300 px-3 py-2 text-[11pt] text-gray-900" },
    };
  },
});

const CustomTableHeader = TableHeader.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      class: { default: "border border-gray-300 px-3 py-2 bg-gray-100 font-semibold text-[11pt] text-gray-900" },
    };
  },
});

const readonlyExtensions = [
  StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
  Underline,
  TextAlign.configure({
    types: ["heading", "paragraph"],
    alignments: ["left", "center", "right", "justify"],
  }),
  CustomTable.configure({
    resizable: false,
    HTMLAttributes: { class: "border-collapse w-full my-4" },
  }),
  TableRow,
  CustomTableCell,
  CustomTableHeader,
  Image.configure({
    inline: true,
    allowBase64: true,
    HTMLAttributes: { class: "max-w-full h-auto my-4 rounded-lg shadow-sm" },
  }),
  DynamicTableExtension,
  DynamicChartExtension,
  PageBreakExtension,
  VariableNodeExtension,
  DynamicBlockExtension,
  SelectedEventsPlaceholderExtension,
];

const editorClassName =
  "min-h-[297mm] outline-none prose prose-base max-w-none focus:outline-none " +
  "[&_h1]:text-3xl [&_h1]:font-normal [&_h1]:mb-3 [&_h1]:mt-6 [&_h1]:text-gray-900 " +
  "[&_h2]:text-2xl [&_h2]:font-normal [&_h2]:mb-2 [&_h2]:mt-5 [&_h2]:text-gray-900 " +
  "[&_h3]:text-xl [&_h3]:font-normal [&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-gray-900 " +
  "[&_p]:text-[11pt] [&_p]:leading-[1.15] [&_p]:mb-[11pt] [&_p]:text-gray-900 " +
  "[&_ul]:list-disc [&_ul]:mb-[11pt] [&_ul]:ml-6 [&_ul]:pl-0 " +
  "[&_ol]:list-decimal [&_ol]:mb-[11pt] [&_ol]:ml-6 [&_ol]:pl-0 " +
  "[&_li]:text-[11pt] [&_li]:leading-[1.15] [&_li]:text-gray-900 [&_li]:mb-0 " +
  "[&_blockquote]:border-l-4 [&_blockquote]:border-gray-300 [&_blockquote]:pl-4 " +
  "[&_blockquote]:my-[11pt] [&_blockquote]:text-[11pt] [&_blockquote]:text-gray-700 [&_blockquote]:italic " +
  "[&_table]:border-collapse [&_table]:w-full [&_table]:my-4 " +
  "[&_td]:border [&_td]:border-gray-300 [&_td]:px-3 [&_td]:py-2 [&_td]:text-[11pt] [&_td]:text-gray-900 " +
  "[&_th]:border [&_th]:border-gray-300 [&_th]:px-3 [&_th]:py-2 [&_th]:bg-gray-100 [&_th]:font-semibold [&_th]:text-[11pt] [&_th]:text-gray-900 " +
  "[&_img]:max-w-full [&_img]:h-auto [&_img]:my-4 " +
  "[&_strong]:font-semibold [&_strong]:text-gray-900 " +
  "[&_em]:italic [&_em]:text-gray-900";

interface BoletinReadOnlyPreviewProps {
  content: string;
}

export function BoletinReadOnlyPreview({ content }: BoletinReadOnlyPreviewProps) {
  const parsedContent = useMemo(() => parseContent(content), [content]);

  const editor = useEditor({
    immediatelyRender: false,
    editable: false,
    extensions: readonlyExtensions,
    content: parsedContent,
    editorProps: {
      attributes: { class: editorClassName },
    },
  });

  if (!editor) return null;

  return (
    <div className="overflow-y-auto flex-1">
      <div className="flex justify-center py-4 px-2">
        <div
          className="bg-white shadow-md origin-top"
          style={{
            width: "210mm",
            minHeight: "297mm",
            padding: "2.54cm",
            transform: "scale(0.45)",
            transformOrigin: "top center",
          }}
        >
          <EditorContent editor={editor} />
        </div>
      </div>
    </div>
  );
}
