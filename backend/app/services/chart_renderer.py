"""
Chart Renderer Server-Side
Renderiza UniversalChartSpec a imágenes usando matplotlib con estilos modernos
Estilo inspirado en Recharts para fidelidad visual con el dashboard web
"""

import io
import logging
import os
from typing import Optional
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image

from app.schemas.chart_spec import (
    UniversalChartSpec,
    LineChartData,
    BarChartData,
    AreaChartData,
    PieChartData,
    PyramidChartData,
    MapChartDataWrapper,
)

logger = logging.getLogger(__name__)

# Configurar estilo moderno tipo Recharts
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Roboto', 'Inter', 'Segoe UI', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelcolor': '#374151',
    'axes.edgecolor': '#E5E7EB',
    'axes.linewidth': 1,
    'axes.grid': True,
    'axes.axisbelow': True,
    'grid.alpha': 0.3,
    'grid.color': '#E5E7EB',
    'grid.linewidth': 0.8,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'xtick.color': '#6B7280',
    'ytick.color': '#6B7280',
    'legend.fontsize': 9,
    'legend.frameon': True,
    'legend.framealpha': 0.95,
    'legend.edgecolor': '#E5E7EB',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
})


class ChartRenderer:
    """
    Renderiza charts desde UniversalChartSpec a imágenes PNG
    100% server-side, sin necesidad de navegador
    """

    def render_to_bytes(self, spec: UniversalChartSpec, dpi: int = 300) -> bytes:
        """
        Renderiza un chart spec a imagen PNG

        Args:
            spec: Especificación universal del chart
            dpi: Resolución de la imagen (default: 150)

        Returns:
            Bytes de la imagen PNG
        """
        try:
            # Determinar tipo de chart y renderizar
            if spec.type == "line":
                return self._render_line_chart(spec, dpi)
            elif spec.type == "bar":
                return self._render_bar_chart(spec, dpi)
            elif spec.type == "area":
                return self._render_area_chart(spec, dpi)
            elif spec.type == "pie":
                return self._render_pie_chart(spec, dpi)
            elif spec.type == "d3_pyramid":
                return self._render_pyramid_chart(spec, dpi)
            elif spec.type == "mapa":
                return self._render_map_chart(spec, dpi)
            else:
                raise ValueError(f"Tipo de chart no soportado: {spec.type}")

        except Exception as e:
            logger.error(f"Error renderizando chart {spec.id}: {e}")
            raise

    def _normalize_color(self, color: Optional[str]) -> Optional[str]:
        """
        Normaliza colores de diferentes formatos a formato hex de matplotlib
        Convierte: rgb(r, g, b), rgba(r, g, b, a) -> #RRGGBB o #RRGGBBAA
        """
        if not color:
            return None

        # Si ya es hex, retornar
        if color.startswith('#'):
            return color

        # Si es rgb() o rgba()
        if color.startswith('rgb'):
            import re
            # Extraer números
            match = re.findall(r'[\d.]+', color)
            if match:
                if len(match) >= 3:
                    r, g, b = int(float(match[0])), int(float(match[1])), int(float(match[2]))
                    # Convertir a hex
                    hex_color = f'#{r:02x}{g:02x}{b:02x}'
                    # Si tiene alpha
                    if len(match) >= 4:
                        alpha = float(match[3])
                        # Convertir alpha de 0-1 a 0-255
                        if alpha <= 1.0:
                            alpha = int(alpha * 255)
                        else:
                            alpha = int(alpha)
                        hex_color += f'{alpha:02x}'
                    return hex_color

        # Si es un color nombrado o formato desconocido, intentar retornar tal cual
        return color

    def _render_line_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """Renderiza line chart"""
        data = spec.data
        if not isinstance(data, LineChartData):
            raise ValueError("Data type mismatch for line chart")

        # Obtener config
        config = spec.config.config if hasattr(spec.config, 'config') else {}
        height = config.height / 100 if config.height else 5
        # Aspect ratio 16:9 para evitar estiramiento
        width = height * 1.6

        # Crear figura
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Plotear datasets
        for dataset in data.data.datasets:
            color = self._normalize_color(dataset.color) if dataset.color else None
            marker = 'o' if config.showPoints else None
            ax.plot(
                data.data.labels,
                dataset.data,
                label=dataset.label,
                color=color,
                marker=marker,
                linewidth=2.5,
                markersize=6
            )

        # Configuración moderna
        ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        if config.showLegend:
            legend = ax.legend(frameon=True, fancybox=True, shadow=False)
            legend.get_frame().set_alpha(0.95)
        if config.showGrid:
            ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

        # Rotar labels si son muchos
        if len(data.data.labels) > 10:
            plt.xticks(rotation=45, ha='right', fontsize=9)

        # Remover spines superiores y derechas
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        # Convertir a bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_bar_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """Renderiza bar chart"""
        data = spec.data
        if not isinstance(data, BarChartData):
            raise ValueError("Data type mismatch for bar chart")

        config = spec.config.config if hasattr(spec.config, 'config') else {}
        height = config.height / 100 if config.height else 5
        # Aspect ratio 16:9
        width = height * 1.6

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        labels = data.data.labels
        x = np.arange(len(labels))
        width_bar = 0.8 / len(data.data.datasets)

        # Plotear cada dataset con colores modernos
        colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
        for i, dataset in enumerate(data.data.datasets):
            offset = (i - len(data.data.datasets) / 2) * width_bar + width_bar / 2
            color = self._normalize_color(dataset.color) if dataset.color else colors_palette[i % len(colors_palette)]
            ax.bar(
                x + offset,
                dataset.data,
                width_bar,
                label=dataset.label,
                color=color,
                alpha=0.9,
                edgecolor='white',
                linewidth=0.5
            )

        ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)

        if config.showLegend and len(data.data.datasets) > 1:
            legend = ax.legend(frameon=True, fancybox=True, shadow=False)
            legend.get_frame().set_alpha(0.95)
        if config.showGrid:
            ax.grid(True, alpha=0.2, axis='y', linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

        # Remover spines superiores y derechas
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_area_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """
        Renderiza area chart con soporte para gráficos mixtos (área + línea)
        Perfecto para corredor endémico con línea de casos actuales
        """
        data = spec.data
        if not isinstance(data, AreaChartData):
            raise ValueError("Data type mismatch for area chart")

        config = spec.config.config if hasattr(spec.config, 'config') else {}
        height = config.height / 100 if config.height else 5
        # Aspect ratio 16:9 para evitar estiramiento
        width = height * 1.6

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Verificar si hay datos
        num_labels = len(data.data.labels)
        has_data = num_labels > 0 and any(
            len(ds.data) > 0 and any(v is not None and v != 0 for v in (
                [d['parsedValue'] if isinstance(d, dict) else d for d in ds.data]
            ))
            for ds in data.data.datasets
        )

        if not has_data:
            # Mostrar mensaje de "No hay datos disponibles" con border
            ax.text(0.5, 0.5, 'No hay datos disponibles para el período seleccionado',
                   ha='center', va='center', fontsize=12, color='#6B7280',
                   transform=ax.transAxes, style='italic',
                   bbox=dict(boxstyle='round,pad=1', facecolor='#F9FAFB', edgecolor='#E5E7EB', linewidth=2))
            ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)
            ax.axis('off')

            # Agregar border alrededor de la figura
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_edgecolor('#E5E7EB')
                spine.set_linewidth(2)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='#E5E7EB')
            plt.close(fig)
            buf.seek(0)
            return buf.read()

        # Extraer valores numéricos de datos (manejar formato mixto)
        def extract_values(dataset_data):
            """Extrae valores numéricos, manejando objetos {source, parsedValue}"""
            values = []
            for val in dataset_data:
                if isinstance(val, dict) and 'parsedValue' in val:
                    values.append(val['parsedValue'])
                else:
                    values.append(val if val is not None else 0)
            return values

        x = np.arange(len(data.data.labels))

        # Plotear datasets
        for i, dataset in enumerate(data.data.datasets):
            # Extraer color o usar paleta moderna
            if dataset.color:
                # Convertir rgba string a color matplotlib
                color = self._normalize_color(dataset.color)
            else:
                # Paleta moderna tipo Recharts
                colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                color = colors_palette[i % len(colors_palette)]

            # Extraer valores
            values = extract_values(dataset.data)

            if dataset.type == "line":
                # Línea sin área (casos actuales)
                ax.plot(
                    x,
                    values,
                    label=dataset.label,
                    color=color,
                    linewidth=3,
                    marker='o',
                    markersize=5,
                    markerfacecolor=color,
                    markeredgecolor='white',
                    markeredgewidth=1.5,
                    zorder=10,  # Encima de las áreas
                    alpha=0.9
                )
            else:
                # Área (percentiles del corredor)
                alpha = config.fillOpacity if hasattr(config, 'fillOpacity') else 0.2
                ax.fill_between(
                    x,
                    values,
                    alpha=alpha,
                    color=color,
                    label=dataset.label,
                    linewidth=0
                )
                # Borde del área
                ax.plot(
                    x,
                    values,
                    color=color,
                    linewidth=1.5,
                    alpha=0.6
                )

        # Título y labels
        ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        if spec.description:
            ax.text(0.5, 1.02, spec.description, transform=ax.transAxes,
                   ha='center', fontsize=9, color='#6B7280', style='italic')

        # Configurar eje X
        # Calcular step para no saturar labels
        num_labels = len(data.data.labels)
        if num_labels > 0:
            step = max(1, num_labels // 10)  # Mostrar ~10 labels max
            tick_positions = list(range(0, num_labels, step))
            # Asegurar que tick_positions no esté vacío
            if len(tick_positions) == 0:
                tick_positions = [0]
            tick_labels = [data.data.labels[i] for i in tick_positions if i < len(data.data.labels)]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
            ax.set_xlabel('Semana Epidemiológica', fontsize=10, color='#374151')
            ax.set_ylabel('Casos', fontsize=10, color='#374151')

        # Leyenda moderna
        if config.showLegend:
            legend = ax.legend(
                loc='upper left',
                bbox_to_anchor=(0, 1),
                frameon=True,
                fancybox=True,
                shadow=False,
                ncol=min(4, len(data.data.datasets))
            )
            legend.get_frame().set_alpha(0.95)

        # Grid sutil
        if config.showGrid:
            ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

        # Remover spines superiores y derechas para look moderno
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_pie_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """Renderiza pie chart con labels mejorados"""
        data = spec.data
        if not isinstance(data, PieChartData):
            raise ValueError("Data type mismatch for pie chart")

        config = spec.config.config if hasattr(spec.config, 'config') else {}
        height = config.height / 100 if config.height else 6
        # Más espacio horizontal para la leyenda
        width = height * 1.4

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Tomar el primer dataset (pie chart solo tiene uno)
        dataset = data.data.datasets[0]

        # Colores modernos
        colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']
        colors = colors_palette[:len(data.data.labels)]

        # Crear pie chart con formato mejorado
        autopct = lambda pct: f'{pct:.1f}%' if pct > 3 else ''  # Solo mostrar % si es > 3%
        wedges, texts, autotexts = ax.pie(
            dataset.data,
            labels=None,  # No poner labels directamente, usar leyenda
            autopct=autopct,
            startangle=90,
            colors=colors,
            explode=[0.02] * len(dataset.data),  # Pequeña separación
            shadow=False,
            textprops={'fontsize': 9, 'weight': 'bold', 'color': 'white'}
        )

        ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)

        # Siempre usar leyenda para evitar overlap
        ax.legend(
            data.data.labels,
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            frameon=True,
            fancybox=True,
            shadow=False,
            fontsize=9
        )

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_pyramid_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """Renderiza population pyramid chart con diseño mejorado y claridad visual"""
        data = spec.data
        if not isinstance(data, PyramidChartData):
            raise ValueError("Data type mismatch for pyramid chart")

        config = spec.config.config if hasattr(spec.config, 'config') else {}
        height = config.height / 100 if config.height else 6
        # Aspect ratio más ancho para mejor visualización
        width = height * 1.8

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Extraer datos por grupo de edad
        age_groups = [p.age_group for p in data.data]
        males = [-p.male for p in data.data]  # Negativos para la izquierda
        females = [p.female for p in data.data]

        # Encontrar el valor máximo para centrar la pirámide
        max_val = max(max(abs(m) for m in males), max(females))

        y_pos = np.arange(len(age_groups))

        # Colores modernos para género
        male_color = '#3B82F6'  # Blue-500
        female_color = '#EC4899'  # Pink-500

        # Crear barras horizontales con mejor estilo
        bar1 = ax.barh(y_pos, males, height=0.8, color=male_color,
                       label='Masculino', alpha=0.85, edgecolor='white', linewidth=0.5)
        bar2 = ax.barh(y_pos, females, height=0.8, color=female_color,
                       label='Femenino', alpha=0.85, edgecolor='white', linewidth=0.5)

        # Labels de grupos de edad EN EL CENTRO
        ax.set_yticks(y_pos)
        ax.set_yticklabels(age_groups, fontsize=9, fontweight='500')

        # Título y descripción
        ax.set_title(spec.title, fontsize=15, fontweight='600', color='#1F2937', pad=15)

        # Label del eje X
        ax.set_xlabel('Número de casos', fontsize=11, fontweight='500', color='#374151')

        # Centrar la pirámide horizontalmente
        ax.set_xlim(-max_val * 1.1, max_val * 1.1)

        # Leyenda visible
        legend = ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=False)
        legend.get_frame().set_alpha(0.95)

        # Grid sutil
        ax.grid(True, alpha=0.2, axis='x', linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

        # Ajustar labels del eje x para mostrar valores ABSOLUTOS
        xticks = ax.get_xticks()
        ax.set_xticklabels([f'{abs(int(x))}' for x in xticks], fontsize=9)

        # Añadir línea vertical en x=0 para claridad
        ax.axvline(x=0, color='#9CA3AF', linewidth=2, linestyle='-', alpha=0.7)

        # Remover spines superiores
        ax.spines['top'].set_visible(False)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _render_map_chart(self, spec: UniversalChartSpec, dpi: int) -> bytes:
        """
        Renderiza mapa geográfico usando el SVG de Chubut
        Muestra el mapa + tabla con datos por departamento
        """
        data = spec.data
        if not isinstance(data, MapChartDataWrapper):
            raise ValueError("Data type mismatch for map chart")

        config = spec.config.config if hasattr(spec.config, 'config') else {}

        # Path al SVG de Chubut
        svg_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'assets',
            'chubut.svg'
        )

        # Convertir SVG a imagen PNG usando svglib + reportlab
        try:
            drawing = svg2rlg(svg_path)
            if drawing:
                # Renderizar SVG a PNG
                svg_img_bytes = renderPM.drawToString(drawing, fmt='PNG', dpi=dpi)
                svg_img = Image.open(io.BytesIO(svg_img_bytes))

                # Crear figura MUCHO MÁS GRANDE (triple de alto) para el mapa
                fig = plt.figure(figsize=(12, 20), dpi=dpi)
                # Mayor spacing entre mapa y tabla
                gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.3)

                # Subplot 1: Mapa SVG (sin título duplicado)
                ax_map = fig.add_subplot(gs[0])
                # Usar aspect='equal' para mantener proporciones originales del SVG
                ax_map.imshow(svg_img, aspect='equal')
                ax_map.axis('off')
                # Título general de la figura
                fig.suptitle(spec.title, fontsize=15, fontweight='600', color='#1F2937', y=0.98)

                # Subplot 2: Tabla con datos (sin título de texto adicional)
                ax_table = fig.add_subplot(gs[1])
                ax_table.axis('tight')
                ax_table.axis('off')

                # Preparar datos de la tabla (top 10 departamentos)
                table_data = []
                for dept in sorted(data.data.departamentos, key=lambda x: x.casos, reverse=True)[:10]:
                    table_data.append([
                        dept.nombre,
                        f"{dept.casos:,}",
                        f"{dept.tasa_incidencia:.2f}"
                    ])

                table = ax_table.table(
                    cellText=table_data,
                    colLabels=['Departamento', 'Casos', 'Tasa/100k hab.'],
                    cellLoc='left',
                    loc='center',
                    colWidths=[0.5, 0.25, 0.25],
                    bbox=[0, 0, 1, 0.9]  # Dejar espacio para el título
                )
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.8)

                # Estilizar header de tabla
                for i in range(3):
                    cell = table[(0, i)]
                    cell.set_facecolor('#3B82F6')
                    cell.set_text_props(weight='bold', color='white')

                # Agregar total de casos como texto
                fig.text(
                    0.5, 0.02,
                    f"Total de casos en la provincia: {data.data.total_casos:,}",
                    ha='center',
                    fontsize=11,
                    fontweight='bold',
                    color='#374151'
                )

                # Convertir a bytes
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                buf.seek(0)
                return buf.read()
            else:
                raise ValueError("No se pudo cargar el SVG")

        except Exception as e:
            logger.warning(f"Error renderizando mapa SVG: {e}. Usando fallback con tabla.")

            # Fallback: solo tabla si el SVG falla
            height = config.height / 100 if config.height else 6
            width = height * 1.5

            fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
            ax.axis('tight')
            ax.axis('off')

            table_data = []
            for dept in data.data.departamentos[:10]:
                table_data.append([
                    dept.nombre,
                    f"{dept.casos}",
                    f"{dept.tasa_incidencia:.2f}"
                ])

            table = ax.table(
                cellText=table_data,
                colLabels=['Departamento', 'Casos', 'Tasa/100k'],
                cellLoc='left',
                loc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)

            ax.set_title(f"{spec.title}\nTotal: {data.data.total_casos} casos",
                        fontsize=14, fontweight='bold', pad=20)

            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            return buf.read()


# Singleton instance
chart_renderer = ChartRenderer()
