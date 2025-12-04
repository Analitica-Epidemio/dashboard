"""
Convertidor de TipTap JSON a HTML.
Convierte el formato JSON de TipTap a HTML para renderizar PDFs.
"""

import html
from typing import Any, Dict, List


def tiptap_to_html(doc: Dict[str, Any]) -> str:
    """Convierte un documento TipTap JSON a HTML."""
    if not doc or doc.get("type") != "doc":
        return ""

    content = doc.get("content", [])
    return render_nodes(content)


def render_nodes(nodes: List[Dict[str, Any]]) -> str:
    """Renderiza una lista de nodos TipTap a HTML."""
    return "".join(render_node(node) for node in nodes)


def render_node(node: Dict[str, Any]) -> str:
    """Renderiza un nodo TipTap individual a HTML."""
    node_type = node.get("type", "")
    attrs = node.get("attrs", {})
    content = node.get("content", [])
    marks = node.get("marks", [])
    text = node.get("text", "")

    # Nodos de texto
    if node_type == "text":
        escaped_text = html.escape(text)
        return apply_marks(escaped_text, marks)

    # Headings
    if node_type == "heading":
        level = attrs.get("level", 1)
        inner = render_nodes(content)
        return f"<h{level}>{inner}</h{level}>"

    # Párrafos
    if node_type == "paragraph":
        inner = render_nodes(content)
        return f"<p>{inner}</p>"

    # Listas
    if node_type == "bulletList":
        inner = render_nodes(content)
        return f"<ul>{inner}</ul>"

    if node_type == "orderedList":
        inner = render_nodes(content)
        return f"<ol>{inner}</ol>"

    if node_type == "listItem":
        inner = render_nodes(content)
        return f"<li>{inner}</li>"

    # Blockquote
    if node_type == "blockquote":
        inner = render_nodes(content)
        return f"<blockquote>{inner}</blockquote>"

    # Horizontal rule
    if node_type == "horizontalRule":
        return "<hr/>"

    # Hard break
    if node_type == "hardBreak":
        return "<br/>"

    # Code block
    if node_type == "codeBlock":
        inner = render_nodes(content)
        return f"<pre><code>{inner}</code></pre>"

    # Tablas
    if node_type == "table":
        inner = render_nodes(content)
        return f'<table style="border-collapse: collapse; width: 100%; font-size: 11px;">{inner}</table>'

    if node_type == "tableRow":
        inner = render_nodes(content)
        return f"<tr>{inner}</tr>"

    if node_type == "tableHeader":
        inner = render_nodes(content)
        return f'<th style="border: 1px solid #ddd; padding: 6px 8px; background: #f5f5f5; font-weight: bold; text-align: left;">{inner}</th>'

    if node_type == "tableCell":
        inner = render_nodes(content)
        return f'<td style="border: 1px solid #ddd; padding: 5px 8px;">{inner}</td>'

    # Imágenes
    if node_type == "image":
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" style="max-width: 100%;"/>'

    # Nodos dinámicos (charts, tables)
    if node_type == "dynamicChart":
        chart_code = attrs.get("chartCode", "")
        evento_ids = attrs.get("eventoIds", "")
        grupo_ids = attrs.get("grupoIds", "")
        title = attrs.get("title", "")
        fecha_desde = attrs.get("fechaDesde", "")
        fecha_hasta = attrs.get("fechaHasta", "")

        return (
            f'<div data-type="dynamic-chart" '
            f'data-chart-code="{html.escape(chart_code)}" '
            f'data-evento-ids="{html.escape(evento_ids)}" '
            f'data-grupo-ids="{html.escape(grupo_ids)}" '
            f'data-title="{html.escape(title)}" '
            f'data-fecha-desde="{html.escape(fecha_desde)}" '
            f'data-fecha-hasta="{html.escape(fecha_hasta)}">'
            f'</div>'
        )

    if node_type == "dynamicTable":
        query_type = attrs.get("queryType", "")
        title = attrs.get("title", "")
        return (
            f'<div data-type="dynamic-table" '
            f'data-query-type="{html.escape(query_type)}" '
            f'data-title="{html.escape(title)}">'
            f'</div>'
        )

    if node_type == "pageBreak":
        return '<div style="page-break-after: always;"></div>'

    # Variable nodes
    if node_type == "variable":
        var_id = attrs.get("variableId", "")
        label = attrs.get("label", var_id)
        return f'<span data-variable="{html.escape(var_id)}">{html.escape(label)}</span>'

    # Fallback: renderizar contenido sin wrapper
    if content:
        return render_nodes(content)

    return ""


def apply_marks(text: str, marks: List[Dict[str, Any]]) -> str:
    """Aplica marcas (bold, italic, etc) al texto."""
    result = text

    for mark in marks:
        mark_type = mark.get("type", "")

        if mark_type == "bold":
            result = f"<strong>{result}</strong>"
        elif mark_type == "italic":
            result = f"<em>{result}</em>"
        elif mark_type == "underline":
            result = f"<u>{result}</u>"
        elif mark_type == "strike":
            result = f"<s>{result}</s>"
        elif mark_type == "code":
            result = f"<code>{result}</code>"
        elif mark_type == "link":
            href = mark.get("attrs", {}).get("href", "")
            result = f'<a href="{html.escape(href)}">{result}</a>'

    return result
