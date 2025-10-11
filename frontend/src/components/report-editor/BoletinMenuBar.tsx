"use client";

import { Editor } from "@tiptap/react";
import {
  Bold,
  Italic,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  List,
  ListOrdered,
  Undo,
  Redo,
  Heading1,
  Heading2,
  Heading3,
  Type,
  Quote,
  Table as TableIcon,
  Image as ImageIcon,
  Database,
  BarChart3,
  FileText,
  Hash,
} from "lucide-react";
import { useCallback, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface BoletinMenuBarProps {
  editor: Editor;
}

export function BoletinMenuBar({ editor }: BoletinMenuBarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addImage = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleImageChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file && file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const src = e.target?.result as string;
          editor.chain().focus().setImage({ src }).run();
        };
        reader.readAsDataURL(file);
      }
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [editor]
  );

  const insertTable = useCallback(() => {
    editor
      .chain()
      .focus()
      .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
      .run();
  }, [editor]);

  const insertDynamicTable = useCallback(() => {
    editor.chain().focus().insertDynamicTable({ queryType: "top_enos" }).run();
  }, [editor]);

  const insertDynamicChart = useCallback(() => {
    editor
      .chain()
      .focus()
      .insertDynamicChart({
        queryType: "corredor_ira",
        chartType: "line",
        height: 300,
      })
      .run();
  }, [editor]);

  const insertPageBreak = useCallback(() => {
    editor.chain().focus().insertPageBreak().run();
  }, [editor]);

  const insertVariable = useCallback(() => {
    editor.chain().focus().insertVariable({ variableId: "año" }).run();
  }, [editor]);

  const getBlockType = () => {
    if (editor.isActive("heading", { level: 1 })) return "Titulo 1";
    if (editor.isActive("heading", { level: 2 })) return "Titulo 2";
    if (editor.isActive("heading", { level: 3 })) return "Titulo 3";
    if (editor.isActive("blockquote")) return "Cita";
    return "Parrafo";
  };

  return (
    <div className="flex flex-wrap items-center gap-1 p-2 bg-muted/30">
      {/* Undo/Redo */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        className="h-8 w-8"
        title="Deshacer"
      >
        <Undo className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        className="h-8 w-8"
        title="Rehacer"
      >
        <Redo className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Block Type */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="h-8">
            <Type className="h-4 w-4 mr-2" />
            {getBlockType()}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem
            onClick={() => editor.chain().focus().setParagraph().run()}
          >
            <Type className="h-4 w-4 mr-2" />
            Parrafo Normal
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 1 }).run()
            }
          >
            <Heading1 className="h-4 w-4 mr-2" />
            Titulo 1
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 2 }).run()
            }
          >
            <Heading2 className="h-4 w-4 mr-2" />
            Titulo 2
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 3 }).run()
            }
          >
            <Heading3 className="h-4 w-4 mr-2" />
            Titulo 3
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
          >
            <Quote className="h-4 w-4 mr-2" />
            Cita
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Text Formatting */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={`h-8 w-8 ${editor.isActive("bold") ? "bg-muted" : ""}`}
        title="Negrita"
      >
        <Bold className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={`h-8 w-8 ${editor.isActive("italic") ? "bg-muted" : ""}`}
        title="Cursiva"
      >
        <Italic className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        className={`h-8 w-8 ${editor.isActive("underline") ? "bg-muted" : ""}`}
        title="Subrayado"
      >
        <Underline className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Lists */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={`h-8 w-8 ${editor.isActive("bulletList") ? "bg-muted" : ""}`}
        title="Lista con vinetas"
      >
        <List className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={`h-8 w-8 ${editor.isActive("orderedList") ? "bg-muted" : ""}`}
        title="Lista numerada"
      >
        <ListOrdered className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Alignment */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().setTextAlign("left").run()}
        className={`h-8 w-8 ${editor.isActive({ textAlign: "left" }) ? "bg-muted" : ""}`}
        title="Alinear izquierda"
      >
        <AlignLeft className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().setTextAlign("center").run()}
        className={`h-8 w-8 ${editor.isActive({ textAlign: "center" }) ? "bg-muted" : ""}`}
        title="Centrar"
      >
        <AlignCenter className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().setTextAlign("right").run()}
        className={`h-8 w-8 ${editor.isActive({ textAlign: "right" }) ? "bg-muted" : ""}`}
        title="Alinear derecha"
      >
        <AlignRight className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().setTextAlign("justify").run()}
        className={`h-8 w-8 ${editor.isActive({ textAlign: "justify" }) ? "bg-muted" : ""}`}
        title="Justificar"
      >
        <AlignJustify className="h-4 w-4" />
      </Button>

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Table */}
      <Button
        variant="ghost"
        size="icon"
        onClick={insertTable}
        className="h-8 w-8"
        title="Insertar Tabla Manual"
      >
        <TableIcon className="h-4 w-4" />
      </Button>

      {/* Image */}
      <Button
        variant="ghost"
        size="icon"
        onClick={addImage}
        className="h-8 w-8"
        title="Insertar Imagen"
      >
        <ImageIcon className="h-4 w-4" />
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageChange}
        className="hidden"
      />

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Dynamic Content */}
      <Button
        variant="default"
        size="sm"
        onClick={insertDynamicTable}
        className="h-8"
        title="Insertar Tabla Dinamica"
      >
        <Database className="h-4 w-4 mr-2" />
        Tabla Dinamica
      </Button>

      <Button
        variant="default"
        size="sm"
        onClick={insertDynamicChart}
        className="h-8"
        title="Insertar Grafico Dinamico"
      >
        <BarChart3 className="h-4 w-4 mr-2" />
        Grafico Dinamico
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={insertPageBreak}
        className="h-8"
        title="Insertar Salto de Pagina"
      >
        <FileText className="h-4 w-4 mr-2" />
        Salto de Pagina
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={insertVariable}
        className="h-8"
        title="Insertar Variable (año, semana, fechas)"
      >
        <Hash className="h-4 w-4 mr-2" />
        Variable
      </Button>
    </div>
  );
}
