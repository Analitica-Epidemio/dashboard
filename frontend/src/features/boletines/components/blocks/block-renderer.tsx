"use client";

import { HeadingBlockEditor } from "./heading-block-editor";
import { ParagraphBlockEditor } from "./paragraph-block-editor";
import { TableBlockEditor } from "./table-block-editor";
import { ChartBlockEditor } from "./chart-block-editor";
import { ImageBlockEditor } from "./image-block-editor";
import { DividerBlockEditor } from "./divider-block-editor";
import { PageBreakBlockEditor } from "./page-break-block-editor";
import type { Block } from "./types";

interface BlockRendererProps {
  block: Block;
  onChange: (block: Block) => void;
  onDelete: (id: string) => void;
}

export function BlockRenderer({ block, onChange, onDelete }: BlockRendererProps) {
  switch (block.type) {
    case "heading":
      return (
        <HeadingBlockEditor
          block={block}
          onChange={onChange}
          onDelete={onDelete}
        />
      );
    case "paragraph":
      return (
        <ParagraphBlockEditor
          block={block}
          onChange={onChange}
          onDelete={onDelete}
        />
      );
    case "table":
      return (
        <TableBlockEditor
          block={block}
          onChange={onChange}
          onDelete={onDelete}
        />
      );
    case "chart":
      return (
        <ChartBlockEditor
          block={block}
          onChange={onChange}
          onDelete={onDelete}
        />
      );
    case "image":
      return (
        <ImageBlockEditor
          block={block}
          onChange={onChange}
          onDelete={onDelete}
        />
      );
    case "divider":
      return <DividerBlockEditor block={block} onDelete={onDelete} />;
    case "pagebreak":
      return <PageBreakBlockEditor block={block} onDelete={onDelete} />;
    default:
      return null;
  }
}
