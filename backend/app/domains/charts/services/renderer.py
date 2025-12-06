"""
Chart Renderer Server-Side
Renderiza EspecificacionGraficoUniversal a imágenes usando matplotlib con estilos modernos
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
from PIL import Image
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from app.domains.charts.schemas import (
    DatosGraficoArea,
    DatosGraficoBarra,
    DatosGraficoLinea,
    WrapperDatosGraficoMapa,
    DatosGraficoTorta,
    DatosGraficoPiramide,
    EspecificacionGraficoUniversal,
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
    Renderiza charts desde EspecificacionGraficoUniversal a imágenes PNG
    100% server-side, sin necesidad de navegador
    """

    def renderizar_a_bytes(self, spec: EspecificacionGraficoUniversal, dpi: int = 300) -> bytes:
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
            if spec.tipo == "line":
                return self._renderizar_grafico_linea(spec, dpi)
            elif spec.tipo == "bar":
                return self._renderizar_grafico_barra(spec, dpi)
            elif spec.tipo == "area":
                return self._renderizar_grafico_area(spec, dpi)
            elif spec.tipo == "pie":
                return self._renderizar_grafico_torta(spec, dpi)
            elif spec.tipo == "d3_pyramid":
                return self._renderizar_grafico_piramide(spec, dpi)
            elif spec.tipo == "mapa":
                return self._renderizar_grafico_mapa(spec, dpi)
            else:
                raise ValueError(f"Tipo de chart no soportado: {spec.tipo}")

        except Exception as e:
            logger.error(f"Error renderizando chart {spec.id}: {e}")
            raise

    def _normalizar_color(self, color: Optional[str]) -> Optional[str]:
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

    def _renderizar_grafico_linea(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """Renderiza line chart"""
        datos = spec.datos
        if not isinstance(datos, DatosGraficoLinea):
            raise ValueError("Data type mismatch for line chart")

        # Obtener config
        config = spec.configuracion.configuracion if hasattr(spec.configuracion, 'configuracion') else {}
        alto = config.alto / 100 if config.alto else 5
        # Aspect ratio 16:9 para evitar estiramiento
        ancho = alto * 1.6

        # Crear figura
        fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)

        # Plotear datasets
        for dataset in datos.datos.conjuntos_datos:
            color = self._normalizar_color(dataset.color) if dataset.color else None
            marker = 'o' if config.mostrar_puntos else None
            ax.plot(
                datos.datos.etiquetas,
                dataset.datos,
                label=dataset.etiqueta,
                color=color,
                marker=marker,
                linewidth=2.5,
                markersize=6
            )

        # Configuración moderna
        ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        if config.mostrar_leyenda:
            legend = ax.legend(frameon=True, fancybox=True, shadow=False)
            legend.get_frame().set_alpha(0.95)
        if config.mostrar_grilla:
            ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

        # Rotar labels si son muchos
        if len(datos.datos.etiquetas) > 10:
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

    def _renderizar_grafico_barra(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """Renderiza bar chart"""
        datos = spec.datos
        if not isinstance(datos, DatosGraficoBarra):
            raise ValueError("Data type mismatch for bar chart")

        config = spec.configuracion.configuracion if hasattr(spec.configuracion, 'configuracion') else {}
        alto = config.alto / 100 if config.alto else 5
        # Aspect ratio 16:9
        ancho = alto * 1.6

        fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)

        etiquetas = datos.datos.etiquetas
        x = np.arange(len(etiquetas))
        width_bar = 0.8 / len(datos.datos.conjuntos_datos)

        # Plotear cada dataset con colores modernos
        colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
        for i, dataset in enumerate(datos.datos.conjuntos_datos):
            offset = (i - len(datos.datos.conjuntos_datos) / 2) * width_bar + width_bar / 2
            color = self._normalizar_color(dataset.color) if dataset.color else colors_palette[i % len(colors_palette)]
            ax.bar(
                x + offset,
                dataset.datos,
                width_bar,
                label=dataset.etiqueta,
                color=color,
                alpha=0.9,
                edgecolor='white',
                linewidth=0.5
            )

        ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=9)

        if config.mostrar_leyenda and len(datos.datos.conjuntos_datos) > 1:
            legend = ax.legend(frameon=True, fancybox=True, shadow=False)
            legend.get_frame().set_alpha(0.95)
        if config.mostrar_grilla:
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

    def _renderizar_grafico_area(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """
        Renderiza area chart con soporte para gráficos mixtos (área + línea)
        Perfecto para corredor endémico con línea de casos actuales
        """
        datos = spec.datos
        if not isinstance(datos, DatosGraficoArea):
            raise ValueError("Data type mismatch for area chart")

        config = spec.configuracion.configuracion if hasattr(spec.configuracion, 'configuracion') else {}
        alto = config.alto / 100 if config.alto else 5
        # Aspect ratio 16:9 para evitar estiramiento
        ancho = alto * 1.6

        fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)

        # Verificar si hay datos
        num_labels = len(datos.datos.etiquetas)
        has_data = num_labels > 0 and any(
            len(ds.datos) > 0 and any(v is not None and v != 0 for v in (
                [d['parsedValue'] if isinstance(d, dict) else d for d in ds.datos]
            ))
            for ds in datos.datos.conjuntos_datos
        )

        if not has_data:
            # Mostrar mensaje de "No hay datos disponibles" con border
            ax.text(0.5, 0.5, 'No hay datos disponibles para el período seleccionado',
                   ha='center', va='center', fontsize=12, color='#6B7280',
                   transform=ax.transAxes, style='italic',
                   bbox=dict(boxstyle='round,pad=1', facecolor='#F9FAFB', edgecolor='#E5E7EB', linewidth=2))
            ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)
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

        x = np.arange(len(datos.datos.etiquetas))

        # Plotear datasets
        for i, dataset in enumerate(datos.datos.conjuntos_datos):
            # Extraer color o usar paleta moderna
            if dataset.color:
                # Convertir rgba string a color matplotlib
                color = self._normalizar_color(dataset.color)
            else:
                # Paleta moderna tipo Recharts
                colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                color = colors_palette[i % len(colors_palette)]

            # Extraer valores
            values = extract_values(dataset.datos)

            if dataset.tipo == "line":
                # Línea sin área (casos actuales)
                ax.plot(
                    x,
                    values,
                    label=dataset.etiqueta,
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
                alpha = config.opacidad_relleno if hasattr(config, 'opacidad_relleno') else 0.2
                ax.fill_between(
                    x,
                    values,
                    alpha=alpha,
                    color=color,
                    label=dataset.etiqueta,
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
        ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)
        if spec.descripcion:
            ax.text(0.5, 1.02, spec.descripcion, transform=ax.transAxes,
                   ha='center', fontsize=9, color='#6B7280', style='italic')

        # Configurar eje X
        # Calcular step para no saturar labels
        num_labels = len(datos.datos.etiquetas)
        if num_labels > 0:
            step = max(1, num_labels // 10)  # Mostrar ~10 labels max
            tick_positions = list(range(0, num_labels, step))
            # Asegurar que tick_positions no esté vacío
            if len(tick_positions) == 0:
                tick_positions = [0]
            tick_labels = [datos.datos.etiquetas[i] for i in tick_positions if i < len(datos.datos.etiquetas)]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
            ax.set_xlabel('Semana Epidemiológica', fontsize=10, color='#374151')
            ax.set_ylabel('Casos', fontsize=10, color='#374151')

        # Leyenda moderna
        if config.mostrar_leyenda:
            legend = ax.legend(
                loc='upper left',
                bbox_to_anchor=(0, 1),
                frameon=True,
                fancybox=True,
                shadow=False,
                ncol=min(4, len(datos.datos.conjuntos_datos))
            )
            legend.get_frame().set_alpha(0.95)

        # Grid sutil
        if config.mostrar_grilla:
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

    def _renderizar_grafico_torta(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """Renderiza pie chart con labels mejorados"""
        datos = spec.datos
        if not isinstance(datos, DatosGraficoTorta):
            raise ValueError("Data type mismatch for pie chart")

        config = spec.configuracion.configuracion if hasattr(spec.configuracion, 'configuracion') else {}
        alto = config.alto / 100 if config.alto else 6
        # Más espacio horizontal para la leyenda
        ancho = alto * 1.4

        fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)

        # Tomar el primer dataset (pie chart solo tiene uno)
        dataset = datos.datos.conjuntos_datos[0]

        # Colores modernos
        colors_palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']
        colors = colors_palette[:len(datos.datos.etiquetas)]

        # Crear pie chart con formato mejorado
        def autopct(pct: float) -> str:
            """Solo mostrar % si es > 3%"""
            return f'{pct:.1f}%' if pct > 3 else ''

        wedges, texts, autotexts = ax.pie(
            dataset.datos,
            labels=None,  # No poner labels directamente, usar leyenda
            autopct=autopct,
            startangle=90,
            colors=colors,
            explode=[0.02] * len(dataset.datos),  # Pequeña separación
            shadow=False,
            textprops={'fontsize': 9, 'weight': 'bold', 'color': 'white'}
        )

        ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)

        # Siempre usar leyenda para evitar overlap
        ax.legend(
            datos.datos.etiquetas,
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

    def _renderizar_grafico_piramide(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """Renderiza population pyramid chart con diseño mejorado y claridad visual"""
        datos = spec.datos
        if not isinstance(datos, DatosGraficoPiramide):
            raise ValueError("Data type mismatch for pyramid chart")

        config = spec.configuracion.configuracion if hasattr(spec.configuracion, 'configuracion') else {}
        alto = config.alto / 100 if config.alto else 6
        # Aspect ratio más ancho para mejor visualización
        ancho = alto * 1.8

        fig, ax = plt.subplots(figsize=(ancho, alto), dpi=dpi)

        # Extraer datos por grupo de edad
        grupos_edad = [p.grupo_edad for p in datos.datos]
        masculinos = [-p.masculino for p in datos.datos]  # Negativos para la izquierda
        femeninos = [p.femenino for p in datos.datos]

        # Encontrar el valor máximo para centrar la pirámide
        max_val = max(max(abs(m) for m in masculinos), max(femeninos))

        y_pos = np.arange(len(grupos_edad))

        # Colores modernos para género
        male_color = '#3B82F6'  # Blue-500
        female_color = '#EC4899'  # Pink-500

        # Crear barras horizontales con mejor estilo
        ax.barh(y_pos, masculinos, height=0.8, color=male_color,
                label='Masculino', alpha=0.85, edgecolor='white', linewidth=0.5)
        ax.barh(y_pos, femeninos, height=0.8, color=female_color,
                label='Femenino', alpha=0.85, edgecolor='white', linewidth=0.5)

        # Labels de grupos de edad EN EL CENTRO
        ax.set_yticks(y_pos)
        ax.set_yticklabels(grupos_edad, fontsize=9, fontweight='500')

        # Título y descripción
        ax.set_title(spec.titulo, fontsize=15, fontweight='600', color='#1F2937', pad=15)

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

    def _renderizar_grafico_mapa(self, spec: EspecificacionGraficoUniversal, dpi: int) -> bytes:
        """
        Renderiza mapa geográfico usando el SVG de Chubut.
        Solo el mapa, sin tabla (la tabla se genera como HTML nativo).
        """
        datos = spec.datos
        if not isinstance(datos, WrapperDatosGraficoMapa):
            raise ValueError("Data type mismatch for map chart")

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

                # Crear figura solo para el mapa
                fig, ax = plt.subplots(figsize=(12, 14), dpi=dpi)

                # Mostrar mapa
                ax.imshow(svg_img, aspect='equal')
                ax.axis('off')

                # Título
                ax.set_title(spec.titulo, fontsize=16, fontweight='600', color='#1F2937', pad=15)

                plt.tight_layout()

                # Convertir a bytes
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                buf.seek(0)
                return buf.read()
            else:
                raise ValueError("No se pudo cargar el SVG")

        except Exception as e:
            logger.warning(f"Error renderizando mapa SVG: {e}. Usando placeholder.")

            # Fallback: placeholder si el SVG falla
            fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)
            ax.text(0.5, 0.5, 'Mapa no disponible',
                   ha='center', va='center', fontsize=14, color='#6B7280')
            ax.axis('off')
            ax.set_title(spec.titulo, fontsize=14, fontweight='bold', pad=20)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            return buf.read()

    def renderizar_tabla_departamentos(self, datos: WrapperDatosGraficoMapa, titulo: str = "", dpi: int = 300) -> bytes:
        """
        Renderiza la tabla de departamentos como imagen separada.
        Tabla ancha que ocupa todo el ancho disponible.

        Args:
            datos: Datos del mapa con departamentos
            titulo: Título opcional para la tabla
            dpi: Resolución

        Returns:
            Bytes de la imagen PNG de la tabla
        """
        # Crear figura ancha para la tabla
        fig_width = 14  # Ancho generoso
        fig_height = 6  # Alto suficiente para ~10 filas

        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
        ax.axis('off')

        # Preparar datos de la tabla (todos los departamentos con casos, ordenados)
        datos_tabla = []
        for dept in sorted(datos.datos.departamentos, key=lambda x: x.casos, reverse=True):
            datos_tabla.append([
                dept.nombre,
                f"{dept.casos:,}",
                f"{dept.tasa_incidencia:.2f}"
            ])

        if not datos_tabla:
            ax.text(0.5, 0.5, 'Sin datos de departamentos',
                   ha='center', va='center', fontsize=12, color='#6B7280')
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            return buf.read()

        # Crear tabla ocupando todo el ancho
        table = ax.table(
            cellText=datos_tabla,
            colLabels=['Departamento', 'Casos', 'Tasa/100k hab.'],
            cellLoc='center',
            loc='center',
            colWidths=[0.5, 0.25, 0.25],
            bbox=[0.05, 0.1, 0.9, 0.85]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.0, 2.2)

        # Estilizar header de tabla
        for i in range(3):
            cell = table[(0, i)]
            cell.set_facecolor('#3B82F6')
            cell.set_text_props(weight='bold', color='white', fontsize=13)

        # Estilizar celdas de datos
        for row_idx in range(1, len(datos_tabla) + 1):
            # Alinear departamento a la izquierda
            table[(row_idx, 0)].set_text_props(ha='left')
            # Alternar colores de fondo
            if row_idx % 2 == 0:
                for col_idx in range(3):
                    table[(row_idx, col_idx)].set_facecolor('#F9FAFB')

        # Título si existe
        if titulo:
            ax.set_title(titulo, fontsize=14, fontweight='600', color='#1F2937', pad=10, loc='left')

        # Total de casos
        fig.text(
            0.5, 0.02,
            f"Total de casos en la provincia: {datos.datos.total_casos:,}",
            ha='center',
            fontsize=12,
            fontweight='bold',
            color='#374151'
        )

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return buf.read()


# Singleton instance
chart_renderer = ChartRenderer()
