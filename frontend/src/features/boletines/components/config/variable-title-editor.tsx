"use client";

/**
 * Mini TipTap editor for block titles with variable support
 * Single line, with variable insertion dropdown
 */

import { useEditor, EditorContent, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Placeholder } from "@tiptap/extension-placeholder";
import { useEffect, useCallback, useMemo, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Hash, ChevronDown } from "lucide-react";
import { VariableNodeExtension, VARIABLE_META } from "./extensions/variable-node";

interface VariableTitleEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  helpText?: string;
  /** Show only event variables (for blocks inside event loop) */
  showEventVariables?: boolean;
  /** Show only base variables (for blocks outside event loop) */
  showBaseVariables?: boolean;
}

// Variables disponibles organizadas por categoría
const BASE_VARIABLES = Object.entries(VARIABLE_META)
  .filter(([, meta]) => meta.category === "base")
  .map(([key, meta]) => ({ key, ...meta }));

const EVENT_VARIABLES = Object.entries(VARIABLE_META)
  .filter(([, meta]) => meta.category === "event")
  .map(([key, meta]) => ({ key, ...meta }));

/**
 * Parse a string title into TipTap JSON content
 * Converts {{ variable }} patterns into variableNode nodes
 */
function parseStringToContent(str: string): JSONContent {
  if (!str) {
    return { type: "doc", content: [{ type: "paragraph", content: [] }] };
  }

  const content: JSONContent[] = [];
  // Match {{ variable_name }}
  const regex = /\{\{\s*(\w+)\s*\}\}/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(str)) !== null) {
    // Add text before the variable
    if (match.index > lastIndex) {
      const textBefore = str.slice(lastIndex, match.index);
      if (textBefore) {
        content.push({ type: "text", text: textBefore });
      }
    }

    // Add the variable node
    content.push({
      type: "variableNode",
      attrs: { variableKey: match[1] },
    });

    lastIndex = regex.lastIndex;
  }

  // Add remaining text after last variable
  if (lastIndex < str.length) {
    const textAfter = str.slice(lastIndex);
    if (textAfter) {
      content.push({ type: "text", text: textAfter });
    }
  }

  return {
    type: "doc",
    content: [
      {
        type: "paragraph",
        content: content.length > 0 ? content : [],
      },
    ],
  };
}

/**
 * Convert TipTap JSON content back to string with {{ variable }} syntax
 */
function contentToString(content: JSONContent): string {
  if (!content?.content?.[0]?.content) return "";

  const paragraph = content.content[0];
  if (!paragraph.content) return "";

  return paragraph.content
    .map((node) => {
      if (node.type === "text") {
        return node.text || "";
      }
      if (node.type === "variableNode") {
        return `{{ ${node.attrs?.variableKey} }}`;
      }
      return "";
    })
    .join("");
}

export function VariableTitleEditor({
  value,
  onChange,
  placeholder = "Título del bloque",
  label = "Título",
  helpText,
  showEventVariables = true,
  showBaseVariables = true,
}: VariableTitleEditorProps) {
  // Track if we're updating from external value to prevent loops
  const isUpdatingFromPropRef = useRef(false);
  // Track the last value we received to detect external changes
  const lastValueRef = useRef(value);

  // Memoize extensions to prevent recreation
  const extensions = useMemo(
    () => [
      StarterKit.configure({
        // Disable features we don't need for single-line title
        heading: false,
        bulletList: false,
        orderedList: false,
        blockquote: false,
        codeBlock: false,
        horizontalRule: false,
        hardBreak: false,
      }),
      VariableNodeExtension,
      Placeholder.configure({
        placeholder,
        emptyEditorClass: "is-editor-empty",
      }),
    ],
    [placeholder]
  );

  const editor = useEditor({
    immediatelyRender: false,
    extensions,
    content: parseStringToContent(value),
    editorProps: {
      attributes: {
        class:
          "min-h-[36px] px-3 py-2 text-sm outline-none [&_.is-editor-empty:first-child]:before:content-[attr(data-placeholder)] [&_.is-editor-empty:first-child]:before:text-muted-foreground [&_.is-editor-empty:first-child]:before:float-left [&_.is-editor-empty:first-child]:before:pointer-events-none",
      },
      // Prevent Enter from creating new lines
      handleKeyDown: (view, event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          return true;
        }
        return false;
      },
    },
    onUpdate: ({ editor }) => {
      // Don't call onChange if we're updating from prop
      if (isUpdatingFromPropRef.current) return;

      const newValue = contentToString(editor.getJSON());
      lastValueRef.current = newValue;
      onChange(newValue);
    },
  });

  // Update editor content when value prop changes externally
  useEffect(() => {
    // Only update if value changed externally (not from our own onChange)
    if (editor && value !== lastValueRef.current) {
      lastValueRef.current = value;
      isUpdatingFromPropRef.current = true;
      editor.commands.setContent(parseStringToContent(value));
      isUpdatingFromPropRef.current = false;
    }
  }, [value, editor]);

  const insertVariable = useCallback(
    (key: string) => {
      if (editor) {
        editor.chain().focus().insertVariable(key).run();
      }
    },
    [editor]
  );

  const hasBaseVars = showBaseVariables && BASE_VARIABLES.length > 0;
  const hasEventVars = showEventVariables && EVENT_VARIABLES.length > 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{label}</Label>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1">
              <Hash className="h-3 w-3" />
              Variables
              <ChevronDown className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64 max-h-[300px] overflow-y-auto">
            {hasBaseVars && (
              <>
                <DropdownMenuLabel className="text-xs text-blue-600">
                  Variables del boletín
                </DropdownMenuLabel>
                {BASE_VARIABLES.map((v) => {
                  const Icon = v.icon;
                  return (
                    <DropdownMenuItem
                      key={v.key}
                      onClick={() => insertVariable(v.key)}
                      className="flex items-center justify-between cursor-pointer"
                    >
                      <span className="flex items-center gap-2 text-sm">
                        <Icon className="h-3.5 w-3.5 text-blue-600" />
                        {v.label}
                      </span>
                      <Badge
                        variant="secondary"
                        className="text-[10px] bg-blue-50 text-blue-600"
                      >
                        {v.example}
                      </Badge>
                    </DropdownMenuItem>
                  );
                })}
              </>
            )}

            {hasBaseVars && hasEventVars && <DropdownMenuSeparator />}

            {hasEventVars && (
              <>
                <DropdownMenuLabel className="text-xs text-violet-600">
                  Variables del evento
                </DropdownMenuLabel>
                {EVENT_VARIABLES.map((v) => {
                  const Icon = v.icon;
                  return (
                    <DropdownMenuItem
                      key={v.key}
                      onClick={() => insertVariable(v.key)}
                      className="flex items-center justify-between cursor-pointer"
                    >
                      <span className="flex items-center gap-2 text-sm">
                        <Icon className="h-3.5 w-3.5 text-violet-600" />
                        {v.label}
                      </span>
                      <Badge
                        variant="secondary"
                        className="text-[10px] bg-violet-50 text-violet-600"
                      >
                        {v.example}
                      </Badge>
                    </DropdownMenuItem>
                  );
                })}
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="border rounded-md bg-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
        <EditorContent editor={editor} />
      </div>

      {helpText && (
        <p className="text-xs text-muted-foreground">{helpText}</p>
      )}
    </div>
  );
}
