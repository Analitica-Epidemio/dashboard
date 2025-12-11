"""Convertir JSON de TipTap a HTML."""

from typing import Any


def tiptap_to_html(doc: dict[str, Any]) -> str:
    """
    Convierte un documento TipTap JSON a HTML.

    Args:
        doc: Documento TipTap con estructura {type: "doc", content: [...]}

    Returns:
        String HTML representando el documento.
    """
    if not isinstance(doc, dict) or doc.get("type") != "doc":
        return ""

    content = doc.get("content", [])
    return _render_nodes(content)


def _render_nodes(nodes: list[dict[str, Any]]) -> str:
    """Renderiza una lista de nodos TipTap a HTML."""
    return "".join(_render_node(node) for node in nodes)


def _render_node(node: dict[str, Any]) -> str:
    """Renderiza un nodo TipTap individual a HTML."""
    node_type = node.get("type", "")
    content = node.get("content", [])
    attrs = node.get("attrs", {})

    # Texto con marcas
    if node_type == "text":
        text = node.get("text", "")
        marks = node.get("marks", [])
        for mark in marks:
            text = _apply_mark(text, mark)
        return text

    # Párrafo
    if node_type == "paragraph":
        inner = _render_nodes(content)
        return f"<p>{inner}</p>\n"

    # Encabezados
    if node_type == "heading":
        level = attrs.get("level", 1)
        inner = _render_nodes(content)
        return f"<h{level}>{inner}</h{level}>\n"

    # Listas
    if node_type == "bulletList":
        inner = _render_nodes(content)
        return f"<ul>{inner}</ul>\n"

    if node_type == "orderedList":
        start = attrs.get("start", 1)
        inner = _render_nodes(content)
        return f'<ol start="{start}">{inner}</ol>\n'

    if node_type == "listItem":
        inner = _render_nodes(content)
        return f"<li>{inner}</li>\n"

    # Citas
    if node_type == "blockquote":
        inner = _render_nodes(content)
        return f"<blockquote>{inner}</blockquote>\n"

    # Código
    if node_type == "codeBlock":
        language = attrs.get("language", "")
        inner = _render_nodes(content)
        return f'<pre><code class="language-{language}">{inner}</code></pre>\n'

    # Horizontal rule
    if node_type == "horizontalRule":
        return "<hr>\n"

    # Imágenes
    if node_type == "image":
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        title = attrs.get("title", "")
        return f'<img src="{src}" alt="{alt}" title="{title}">\n'

    # Hard break
    if node_type == "hardBreak":
        return "<br>\n"

    # Tabla
    if node_type == "table":
        inner = _render_nodes(content)
        return f"<table>{inner}</table>\n"

    if node_type == "tableRow":
        inner = _render_nodes(content)
        return f"<tr>{inner}</tr>\n"

    if node_type == "tableCell":
        inner = _render_nodes(content)
        colspan = attrs.get("colspan", 1)
        rowspan = attrs.get("rowspan", 1)
        attrs_str = ""
        if colspan > 1:
            attrs_str += f' colspan="{colspan}"'
        if rowspan > 1:
            attrs_str += f' rowspan="{rowspan}"'
        return f"<td{attrs_str}>{inner}</td>"

    if node_type == "tableHeader":
        inner = _render_nodes(content)
        return f"<th>{inner}</th>"

    # Default: renderizar contenido sin wrapper
    return _render_nodes(content)


def _apply_mark(text: str, mark: dict[str, Any]) -> str:
    """Aplica una marca TipTap al texto."""
    mark_type = mark.get("type", "")
    attrs = mark.get("attrs", {})

    if mark_type == "bold":
        return f"<strong>{text}</strong>"

    if mark_type == "italic":
        return f"<em>{text}</em>"

    if mark_type == "strike":
        return f"<s>{text}</s>"

    if mark_type == "underline":
        return f"<u>{text}</u>"

    if mark_type == "code":
        return f"<code>{text}</code>"

    if mark_type == "link":
        href = attrs.get("href", "")
        target = attrs.get("target", "_blank")
        return f'<a href="{href}" target="{target}">{text}</a>'

    if mark_type == "textStyle":
        styles = []
        if "color" in attrs:
            styles.append(f"color: {attrs['color']}")
        if "backgroundColor" in attrs:
            styles.append(f"background-color: {attrs['backgroundColor']}")
        if styles:
            return f'<span style="{"; ".join(styles)}">{text}</span>'

    if mark_type == "highlight":
        color = attrs.get("color", "yellow")
        return f'<mark style="background-color: {color}">{text}</mark>'

    return text
