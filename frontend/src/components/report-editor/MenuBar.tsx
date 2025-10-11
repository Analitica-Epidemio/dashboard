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
  BracesIcon,
  Table as TableIcon,
  Image as ImageIcon,
} from "lucide-react";
import { useCallback, useRef } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { insertVariable } from "./VariableExtension";

const AVAILABLE_VARIABLES = [
  { key: "disease_name", label: "Nombre de Enfermedad", description: "Ej: Dengue, COVID-19", emoji: "🦠", type: "basic", category: "Información Básica" },
  { key: "date_from", label: "Fecha Desde", description: "Fecha de inicio del período", emoji: "📅", type: "basic", category: "Información Básica" },
  { key: "date_to", label: "Fecha Hasta", description: "Fecha de fin del período", emoji: "🗓️", type: "basic", category: "Información Básica" },
  { key: "generated_date", label: "Fecha de Generación", description: "Fecha en que se creó este reporte", emoji: "📆", type: "basic", category: "Información Básica" },
  { key: "total_cases", label: "Total de Casos", description: "Número total de casos notificados", emoji: "📊", type: "stat", category: "Estadísticas" },
  { key: "confirmed", label: "Casos Confirmados", description: "Casos confirmados por laboratorio", emoji: "✅", type: "stat", category: "Estadísticas" },
  { key: "suspected", label: "Casos Sospechosos", description: "Casos en investigación", emoji: "🔍", type: "stat", category: "Estadísticas" },
  { key: "discarded", label: "Casos Descartados", description: "Casos descartados", emoji: "❌", type: "stat", category: "Estadísticas" },
  { key: "deaths", label: "Fallecidos", description: "Número de fallecimientos", emoji: "💔", type: "stat", category: "Estadísticas" },
  { key: "active_cases", label: "Casos Activos", description: "Casos actualmente en tratamiento", emoji: "🏥", type: "stat", category: "Estadísticas" },
  { key: "recovered", label: "Recuperados", description: "Personas recuperadas", emoji: "💚", type: "stat", category: "Estadísticas" },
  { key: "chart_temporal", label: "GRÁFICO: Evolución Temporal", description: "Gráfico de evolución de casos en el tiempo", emoji: "📈", type: "chart", category: "Gráficos" },
  { key: "chart_geographic", label: "GRÁFICO: Distribución Geográfica", description: "Mapa con distribución de casos por zona", emoji: "🗺️", type: "chart", category: "Gráficos" },
  { key: "chart_age_distribution", label: "GRÁFICO: Distribución por Edad", description: "Gráfico de casos por grupos etarios", emoji: "👥", type: "chart", category: "Gráficos" },
  { key: "chart_gender_distribution", label: "GRÁFICO: Distribución por Sexo", description: "Gráfico de casos por sexo", emoji: "⚧️", type: "chart", category: "Gráficos" },
];

interface MenuBarProps {
  editor: Editor;
}

export function MenuBar({ editor }: MenuBarProps) {
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
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
  }, [editor]);

  const getBlockType = () => {
    if (editor.isActive("heading", { level: 1 })) return "Título 1";
    if (editor.isActive("heading", { level: 2 })) return "Título 2";
    if (editor.isActive("heading", { level: 3 })) return "Título 3";
    if (editor.isActive("blockquote")) return "Cita";
    return "Párrafo";
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
          <DropdownMenuItem onClick={() => editor.chain().focus().setParagraph().run()}>
            <Type className="h-4 w-4 mr-2" />
            Párrafo Normal
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}>
            <Heading1 className="h-4 w-4 mr-2" />
            Título 1
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}>
            <Heading2 className="h-4 w-4 mr-2" />
            Título 2
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}>
            <Heading3 className="h-4 w-4 mr-2" />
            Título 3
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => editor.chain().focus().toggleBlockquote().run()}>
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
        title="Lista con viñetas"
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
        title="Insertar Tabla"
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

      {/* Variables */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="default" size="sm" className="h-8">
            <BracesIcon className="h-4 w-4 mr-2" />
            Insertar Variable
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-64 max-h-96 overflow-y-auto">
          {Object.entries(
            AVAILABLE_VARIABLES.reduce((acc, variable) => {
              if (!acc[variable.category]) {
                acc[variable.category] = [];
              }
              acc[variable.category].push(variable);
              return acc;
            }, {} as Record<string, typeof AVAILABLE_VARIABLES>)
          ).map(([category, variables]) => (
            <div key={category}>
              <DropdownMenuLabel className="text-xs text-muted-foreground">
                {category}
              </DropdownMenuLabel>
              {variables.map((variable) => (
                <DropdownMenuItem
                  key={variable.key}
                  onClick={() => insertVariable(editor, variable.key, variable.label, variable.emoji, variable.type)}
                  className="text-sm flex-col items-start py-2 px-3"
                >
                  <div className="flex items-center gap-2 w-full">
                    <span className="text-base">{variable.emoji}</span>
                    <span className="font-medium">{variable.label}</span>
                  </div>
                  <div className="text-xs text-muted-foreground ml-7">{variable.description}</div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
            </div>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
