"""
Generador de boletines.

Genera boletines completos usando:
- BoletinSeccion / BoletinBloque para configuración
- BloqueQueryAdapter para datos
- TipTap JSON para contenido renderizable
"""

from typing import Any

from sqlmodel import Session, col, select

from app.domains.boletines.models import BoletinInstance, BoletinSeccion
from app.domains.boletines.services.adapter import (
    BloqueQueryAdapter,
    BloqueResultado,
    BoletinContexto,
)


class BoletinGenerator:
    """
    Generador de boletines epidemiológicos.

    Flujo:
    1. Obtener secciones activas ordenadas
    2. Para cada sección, obtener bloques activos
    3. Ejecutar cada bloque via BloqueQueryAdapter
    4. Generar TipTap JSON con resultados
    5. Crear BoletinInstance con el contenido
    """

    def __init__(self, session: Session):
        self.session = session
        self.adapter = BloqueQueryAdapter(session)

    def generar(
        self,
        semana: int,
        anio: int,
        num_semanas: int = 4,
        secciones_slugs: list[str] | None = None,
    ) -> BoletinInstance:
        """
        Genera un boletín completo.

        Args:
            semana: Semana epidemiológica actual
            anio: Año epidemiológico
            num_semanas: Ventana de semanas para datos recientes
            secciones_slugs: Lista de slugs de secciones a incluir (None = todas)

        Returns:
            BoletinInstance con el boletín generado
        """
        contexto = BoletinContexto(
            semana_actual=semana,
            anio_actual=anio,
            num_semanas=num_semanas,
        )

        # Obtener secciones
        secciones = self._get_secciones(secciones_slugs)

        # Generar contenido
        contenido_secciones = []
        datos_bloques: dict[str, Any] = {}

        for seccion in secciones:
            seccion_content = self._generar_seccion(seccion, contexto, datos_bloques)
            contenido_secciones.append(seccion_content)

        # Crear documento TipTap
        tiptap_doc = self._crear_documento_tiptap(
            contenido_secciones,
            contexto,
        )

        # Crear instancia de boletín
        instance = BoletinInstance(
            name=f"Boletín Epidemiológico SE {semana} - {anio}",
            parameters={
                "semana": semana,
                "anio": anio,
                "num_semanas": num_semanas,
                "secciones": secciones_slugs,
            },
            template_snapshot={
                "version": "v2",
                "secciones": [s.slug for s in secciones],
                "tiptap_doc": tiptap_doc,
                "bloques_data": datos_bloques,
            },
            content=None,  # Se llenará con HTML renderizado
        )

        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)

        return instance

    def _get_secciones(self, slugs: list[str] | None) -> list[BoletinSeccion]:
        """Obtiene secciones activas ordenadas."""
        stmt = (
            select(BoletinSeccion)
            .where(col(BoletinSeccion.activo).is_(True))
            .order_by(col(BoletinSeccion.orden))
        )

        if slugs:
            stmt = stmt.where(col(BoletinSeccion.slug).in_(slugs))

        return list(self.session.execute(stmt).scalars().all())

    def _generar_seccion(
        self,
        seccion: BoletinSeccion,
        contexto: BoletinContexto,
        datos_bloques: dict[str, Any],
    ) -> dict[str, Any]:
        """Genera el contenido de una sección."""
        bloques_content = []

        for bloque in seccion.bloques:
            if not bloque.activo:
                continue

            # Ejecutar bloque
            resultado = self.adapter.ejecutar_bloque(bloque, contexto)

            # Guardar datos
            datos_bloques[bloque.slug] = {
                "titulo": resultado.titulo,
                "tipo_visualizacion": resultado.tipo_visualizacion,
                "series": resultado.series,
                "config_visual": resultado.config_visual,
                "metadata": resultado.metadata,
            }

            # Generar TipTap para el bloque
            bloque_content = self._bloque_to_tiptap(resultado)
            bloques_content.append(bloque_content)

        return {
            "slug": seccion.slug,
            "titulo": seccion.titulo,
            "contenido_intro": seccion.contenido_intro,
            "bloques": bloques_content,
        }

    def _bloque_to_tiptap(self, resultado: BloqueResultado) -> dict[str, Any]:
        """Convierte un resultado de bloque a TipTap JSON."""
        return {
            "type": "dynamicBlock",
            "attrs": {
                "blockId": resultado.slug,
                "blockType": resultado.metadata.get("tipo_bloque"),
                "renderType": resultado.tipo_visualizacion,
                "titulo": resultado.titulo,
                "data": {
                    "series": resultado.series,
                    "config_visual": resultado.config_visual,
                },
            },
        }

    def _crear_documento_tiptap(
        self,
        secciones: list[dict[str, Any]],
        contexto: BoletinContexto,
    ) -> dict[str, Any]:
        """Crea el documento TipTap completo."""
        content = []

        # Portada
        content.extend(self._crear_portada(contexto))

        # Secciones
        for seccion in secciones:
            # Título de sección
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": seccion["titulo"]}],
                }
            )

            # Contenido introductorio (si existe)
            if seccion.get("contenido_intro"):
                intro = seccion["contenido_intro"]
                if isinstance(intro, dict) and "content" in intro:
                    content.extend(intro["content"])

            # Bloques de la sección
            for bloque in seccion["bloques"]:
                content.append(bloque)

            # Separador
            content.append({"type": "horizontalRule"})

        # Metodología
        content.extend(self._crear_metodologia())

        return {
            "type": "doc",
            "content": content,
        }

    def _crear_portada(self, contexto: BoletinContexto) -> list[dict[str, Any]]:
        """Genera la portada del boletín."""
        return [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Boletín Epidemiológico Semanal"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Provincia del Chubut - Año {contexto.anio_actual}",
                    },
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Semana Epidemiológica {contexto.semana_actual}",
                    },
                ],
            },
            {"type": "horizontalRule"},
        ]

    def _crear_metodologia(self) -> list[dict[str, Any]]:
        """Genera la sección de metodología."""
        return [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Metodología Utilizada"}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Fuente: SNVS2.0 - SISA"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Los datos provienen del Sistema Nacional de Vigilancia de la Salud (SNVS 2.0). "
                            "Para la construcción de los corredores endémicos, se utilizan los años 2018, 2019, "
                            "2022, 2023 y 2024 (excluyendo los años de pandemia de COVID-19)."
                        ),
                    }
                ],
            },
        ]


def generar_boletin(
    session: Session,
    semana: int,
    anio: int,
    num_semanas: int = 4,
    secciones: list[str] | None = None,
) -> BoletinInstance:
    """
    Función de conveniencia para generar un boletín.

    Args:
        session: Sesión de BD
        semana: Semana epidemiológica
        anio: Año epidemiológico
        num_semanas: Ventana de semanas
        secciones: Slugs de secciones a incluir (None = todas)

    Returns:
        BoletinInstance generado
    """
    generator = BoletinGenerator(session)
    return generator.generar(semana, anio, num_semanas, secciones)
