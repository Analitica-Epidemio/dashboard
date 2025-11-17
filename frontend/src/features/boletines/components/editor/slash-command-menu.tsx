"use client";

import { useEffect, useState, forwardRef, useImperativeHandle } from "react";
import { Editor } from "@tiptap/core";
import {
  Heading1,
  Heading2,
  Heading3,
  Type,
  BarChart3,
  Table,
  Variable,
  Scissors,
} from "lucide-react";

export interface SlashCommandItem {
  title: string;
  description: string;
  icon: React.ReactNode;
  command: () => void;
}

interface SlashCommandMenuProps {
  items: SlashCommandItem[];
  command: (item: SlashCommandItem) => void;
}

export const SlashCommandMenu = forwardRef<
  { onKeyDown: (event: KeyboardEvent) => boolean },
  SlashCommandMenuProps
>((props, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    setSelectedIndex(0);
  }, [props.items]);

  const selectItem = (index: number) => {
    const item = props.items[index];
    if (item) {
      props.command(item);
    }
  };

  useImperativeHandle(ref, () => ({
    onKeyDown: (event: KeyboardEvent) => {
      if (event.key === "ArrowUp") {
        setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length);
        return true;
      }

      if (event.key === "ArrowDown") {
        setSelectedIndex((selectedIndex + 1) % props.items.length);
        return true;
      }

      if (event.key === "Enter") {
        selectItem(selectedIndex);
        return true;
      }

      return false;
    },
  }));

  if (props.items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg border p-3 min-w-[280px]">
        <div className="text-sm text-gray-500">No hay resultados</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border overflow-hidden min-w-[320px]">
      {props.items.map((item, index) => (
        <button
          key={index}
          type="button"
          className={`w-full flex items-start gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors ${
            index === selectedIndex ? "bg-blue-50" : ""
          }`}
          onClick={() => selectItem(index)}
        >
          <div className="mt-0.5 text-gray-500">{item.icon}</div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-900">{item.title}</div>
            <div className="text-xs text-gray-500 truncate">{item.description}</div>
          </div>
        </button>
      ))}
    </div>
  );
});

SlashCommandMenu.displayName = "SlashCommandMenu";

// Command items builder
export const getSlashCommandItems = (
  editor: Editor,
  onOpenChartDialog: () => void,
  onOpenTableDialog: () => void,
  onOpenVariableDialog: () => void
): SlashCommandItem[] => {
  return [
    {
      title: "Título 1",
      description: "Título grande",
      icon: <Heading1 className="w-5 h-5" />,
      command: () => {
        editor.chain().focus().setHeading({ level: 1 }).run();
      },
    },
    {
      title: "Título 2",
      description: "Título mediano",
      icon: <Heading2 className="w-5 h-5" />,
      command: () => {
        editor.chain().focus().setHeading({ level: 2 }).run();
      },
    },
    {
      title: "Título 3",
      description: "Título pequeño",
      icon: <Heading3 className="w-5 h-5" />,
      command: () => {
        editor.chain().focus().setHeading({ level: 3 }).run();
      },
    },
    {
      title: "Texto",
      description: "Párrafo normal",
      icon: <Type className="w-5 h-5" />,
      command: () => {
        editor.chain().focus().setParagraph().run();
      },
    },
    {
      title: "Gráfico Dinámico",
      description: "Insertar gráfico con datos de query",
      icon: <BarChart3 className="w-5 h-5" />,
      command: onOpenChartDialog,
    },
    {
      title: "Tabla Dinámica",
      description: "Insertar tabla con datos de query",
      icon: <Table className="w-5 h-5" />,
      command: onOpenTableDialog,
    },
    {
      title: "Variable",
      description: "Insertar variable (año, semana, etc.)",
      icon: <Variable className="w-5 h-5" />,
      command: onOpenVariableDialog,
    },
    {
      title: "Salto de Página",
      description: "Insertar salto de página",
      icon: <Scissors className="w-5 h-5" />,
      command: () => {
        editor.chain().focus().setPageBreak().run();
      },
    },
  ];
};
