import { Extension, Editor, Range } from "@tiptap/core";
import Suggestion, { SuggestionOptions } from "@tiptap/suggestion";
import { ReactRenderer } from "@tiptap/react";
import tippy, { Instance as TippyInstance } from "tippy.js";
import { SlashCommandMenu, SlashCommandItem } from "../slash-command-menu";

export const SlashCommandExtension = (
  onOpenChartDialog: () => void
) =>
  Extension.create({
    name: "slashCommand",

    addOptions() {
      return {
        suggestion: {
          char: "/",
          startOfLine: false,
          command: ({
            editor,
            range,
            props
          }: {
            editor: Editor;
            range: Range;
            props: { command: (args: { editor: Editor; range: Range }) => void }
          }) => {
            // Delete the "/" character
            editor.commands.deleteRange(range);
            // Execute the command
            props.command({ editor, range });
          },
        } as Partial<SuggestionOptions>,
      };
    },

    addProseMirrorPlugins() {
      return [
        Suggestion({
          editor: this.editor,
          ...this.options.suggestion,
          items: ({ query }: { query: string }) => {
            const items: SlashCommandItem[] = [
              {
                title: "Título 1",
                description: "Título grande",
                icon: "H1",
                command: () => {
                  this.editor.chain().focus().setHeading({ level: 1 }).run();
                },
              },
              {
                title: "Título 2",
                description: "Título mediano",
                icon: "H2",
                command: () => {
                  this.editor.chain().focus().setHeading({ level: 2 }).run();
                },
              },
              {
                title: "Título 3",
                description: "Título pequeño",
                icon: "H3",
                command: () => {
                  this.editor.chain().focus().setHeading({ level: 3 }).run();
                },
              },
              {
                title: "Texto",
                description: "Párrafo normal",
                icon: "T",
                command: () => {
                  this.editor.chain().focus().setParagraph().run();
                },
              },
              {
                title: "Gráfico",
                description: "Insertar gráfico dinámico",
                icon: "📊",
                command: onOpenChartDialog,
              },
              {
                title: "Salto de Página",
                description: "Insertar salto de página",
                icon: "✂️",
                command: () => {
                  this.editor
                    .chain()
                    .focus()
                    .insertContent({ type: "pageBreak" })
                    .run();
                },
              },
            ];

            return items.filter((item) =>
              item.title.toLowerCase().includes(query.toLowerCase())
            );
          },
          render: () => {
            let component: ReactRenderer;
            let popup: TippyInstance[];

            return {
              onStart: (props: { editor: Editor; clientRect?: () => DOMRect }) => {
                component = new ReactRenderer(SlashCommandMenu, {
                  props,
                  editor: props.editor,
                });

                if (!props.clientRect) {
                  return;
                }

                popup = tippy("body", {
                  getReferenceClientRect: props.clientRect,
                  appendTo: () => document.body,
                  content: component.element,
                  showOnCreate: true,
                  interactive: true,
                  trigger: "manual",
                  placement: "bottom-start",
                });
              },

              onUpdate(props: { editor: Editor; clientRect?: () => DOMRect }) {
                component.updateProps(props);

                if (!props.clientRect) {
                  return;
                }

                popup[0].setProps({
                  getReferenceClientRect: props.clientRect,
                });
              },

              onKeyDown(props: { event: KeyboardEvent }) {
                if (props.event.key === "Escape") {
                  popup[0].hide();
                  return true;
                }

                return (component.ref as { onKeyDown?: (event: KeyboardEvent) => boolean })?.onKeyDown?.(props.event) || false;
              },

              onExit() {
                popup[0].destroy();
                component.destroy();
              },
            };
          },
        }),
      ];
    },
  });
