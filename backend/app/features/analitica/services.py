"""
Servicios para Analytics - lógica de negocio para visualizaciones epidemiológicas.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domains.estrategias.models import TipoClasificacion
from app.domains.eventos_epidemiologicos.eventos.models import Evento, TipoEno

from .schemas import (
    ConfiguracionVisualizacion,
    DatosVisualizacionRequest,
    DatosVisualizacionResponse,
    EventoDentroGrupo,
    GrupoEvento,
    GrupoEventoResponse,
    ListaGruposResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Servicio para manejo de analytics y visualizaciones."""

    def __init__(self, session: Session):
        self.session = session

        # Configuración estática basada en el proyecto anterior
        self.grupos_config = self._get_grupos_config()
        self.graficos_config = self._get_graficos_config()

    def _get_grupos_config(self) -> Dict[str, Dict]:
        """
        Configuración de grupos basada en epidemiologia_chubut/filters/eventos_config.py
        """
        return {
            # Eventos Simples
            "Meningoencefalitis": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "notificados", "todos"],
                "orden": 1,
            },
            "SUH - Sindrome Urémico Hemolítico": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "notificados", "todos"],
                "orden": 2,
            },
            "Hidatidosis": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "notificados", "todos"],
                "graficos_especiales": ["grafico_edad_departamento"],
                "orden": 3,
            },
            "Coqueluche": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "sospechosos", "todos"],
                "orden": 4,
            },
            "Intento de Suicidio": {
                "tipo": "simple",
                "clasificaciones": [
                    "todos",
                    "con_resultado_mortal",
                    "sin_resultado_mortal",
                ],
                "graficos_especiales": [
                    "grafico_intento_suicidio_mecanismo",
                    "grafico_intento_suicidio_lugar",
                ],
                "orden": 5,
            },
            "Dengue": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "sospechosos"],
                "orden": 6,
            },
            "Rabia animal": {
                "tipo": "simple",
                "clasificaciones": ["confirmados", "sospechosos", "todos"],
                "graficos_especiales": [
                    "grafico_rabia_animal_comparacion",
                    "grafico_por_contagios",
                ],
                "orden": 7,
            },
            # Grupos de Eventos
            "Sífilis": {
                "tipo": "grupo",
                "clasificaciones": ["confirmados", "notificados", "todos"],
                "eventos": [
                    "Sífilis",
                    "Sífilis congénita",
                    "Sífilis en personas gestantes",
                    "Sífilis - RN expuesto en investigación",
                ],
                "orden": 10,
            },
            "Chagas": {
                "tipo": "grupo",
                "clasificaciones": ["todos"],
                "eventos": ["Chagas agudo congénito", "Chagas en personas gestantes"],
                "orden": 11,
            },
            "Infecciones Respiratorias Agudas (IRA)": {
                "tipo": "grupo",
                "clasificaciones": ["confirmados"],
                "graficos_especiales": [
                    "graficar_curva_epidemiologica",
                    "curva_epi_subtipos_influenza",
                    "graficar_proporcion_ira",
                ],
                "eventos": [
                    "Infecciones Respiratorias Agudas (IRA)",
                    "Estudio de SARS-COV-2 en situaciones especiales",
                    "COVID-19 - Delta",
                    "IRA en unidades centinela",
                ],
                "orden": 12,
            },
            "Hantavirus": {
                "tipo": "grupo",
                "clasificaciones": ["todos"],
                "eventos": [
                    "Hantavirosis",
                    "Hantavirus en estudio de contactos estrechos",
                ],
                "orden": 13,
            },
        }

    def _get_graficos_config(self) -> List[ConfiguracionVisualizacion]:
        """Configuración de gráficos disponibles."""
        return [
            ConfiguracionVisualizacion(
                id="casos_por_edad",
                nombre="Casos por grupo etario",
                tipo="bar",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="casos_por_ugd",
                nombre="Casos por Zona UGD (tasa)",
                tipo="bar",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="torta_ugd",
                nombre="Casos por Zona UGD (torta)",
                tipo="pie",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="torta_sexo",
                nombre="Sexo (Torta)",
                tipo="pie",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="casos_mensual",
                nombre="Casos por meses",
                tipo="line",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="historicos",
                nombre="Históricos",
                tipo="line",
                disponible_para_todos=True,
            ),
            ConfiguracionVisualizacion(
                id="tabla", nombre="Tabla", tipo="table", disponible_para_todos=True
            ),
            ConfiguracionVisualizacion(
                id="corredor_endemico",
                nombre="Corredor endémico",
                tipo="area",
                disponible_para_todos=True,
            ),
            # Gráficos especiales
            ConfiguracionVisualizacion(
                id="curva_epidemiologica",
                nombre="Curva epidemiológica",
                tipo="line",
                disponible_para_grupos=["Infecciones Respiratorias Agudas (IRA)"],
                disponible_para_todos=False,
            ),
            ConfiguracionVisualizacion(
                id="grafico_edad_departamento",
                nombre="Casos edad y departamento",
                tipo="heatmap",
                disponible_para_grupos=["Hidatidosis"],
                disponible_para_todos=False,
            ),
            ConfiguracionVisualizacion(
                id="grafico_rabia_animal_comparacion",
                nombre="Comparación sospechosos - confirmados",
                tipo="bar",
                disponible_para_grupos=["Rabia animal"],
                disponible_para_todos=False,
            ),
        ]

    async def get_grupos(self) -> ListaGruposResponse:
        """Obtiene la lista de grupos disponibles."""
        grupos = []

        for nombre, config in self.grupos_config.items():
            # Buscar en TipoEno si existe este grupo/evento
            tipo_eno = (
                self.session.query(TipoEno).filter(TipoEno.nombre == nombre).first()
            )

            grupo = GrupoEvento(
                id=tipo_eno.id if tipo_eno else hash(nombre) % 10000,  # ID temporal
                nombre=nombre,
                tipo=config["tipo"],
                descripcion=f"Grupo de eventos epidemiológicos: {nombre}",
                activo=True,
                clasificaciones_disponibles=config["clasificaciones"],
                graficos_especiales=config.get("graficos_especiales", []),
                orden=config.get("orden", 100),
            )
            grupos.append(grupo)

        # Ordenar por el campo orden
        grupos.sort(key=lambda x: x.orden)

        return ListaGruposResponse(grupos=grupos, total=len(grupos))

    async def get_grupo_detalle(self, grupo_id: int) -> Optional[GrupoEventoResponse]:
        """Obtiene el detalle de un grupo específico con sus eventos."""

        # Buscar el grupo en la configuración
        grupo_config = None
        grupo_nombre = None

        for nombre, config in self.grupos_config.items():
            tipo_eno = (
                self.session.query(TipoEno).filter(TipoEno.nombre == nombre).first()
            )
            if (tipo_eno and tipo_eno.id == grupo_id) or hash(
                nombre
            ) % 10000 == grupo_id:
                grupo_config = config
                grupo_nombre = nombre
                break

        if not grupo_config:
            return None

        grupo = GrupoEvento(
            id=grupo_id,
            nombre=grupo_nombre,
            tipo=grupo_config["tipo"],
            descripcion=f"Grupo de eventos epidemiológicos: {grupo_nombre}",
            activo=True,
            clasificaciones_disponibles=grupo_config["clasificaciones"],
            graficos_especiales=grupo_config.get("graficos_especiales", []),
            orden=grupo_config.get("orden", 100),
        )

        # Obtener eventos del grupo
        eventos = []
        if grupo_config["tipo"] == "grupo":
            for evento_nombre in grupo_config.get("eventos", []):
                tipo_eno_evento = (
                    self.session.query(TipoEno)
                    .filter(TipoEno.nombre == evento_nombre)
                    .first()
                )

                if tipo_eno_evento:
                    # Obtener estadísticas básicas
                    total_query = self.session.query(func.count(Evento.id)).filter(
                        Evento.id_tipo_eno == tipo_eno_evento.id
                    )
                    total_casos = total_query.scalar() or 0

                    confirmados_query = self.session.query(
                        func.count(Evento.id)
                    ).filter(
                        Evento.id_tipo_eno == tipo_eno_evento.id,
                        Evento.clasificacion_estrategia == TipoClasificacion.CONFIRMADOS,
                    )
                    casos_confirmados = confirmados_query.scalar() or 0

                    sospechosos_query = self.session.query(
                        func.count(Evento.id)
                    ).filter(
                        Evento.id_tipo_eno == tipo_eno_evento.id,
                        Evento.clasificacion_estrategia == TipoClasificacion.SOSPECHOSOS,
                    )
                    casos_sospechosos = sospechosos_query.scalar() or 0

                    ultimo_caso_query = self.session.query(
                        func.max(Evento.fecha_minima_evento)
                    ).filter(Evento.id_tipo_eno == tipo_eno_evento.id)
                    ultimo_caso = ultimo_caso_query.scalar()

                    evento = EventoDentroGrupo(
                        id=tipo_eno_evento.id,
                        tipo_eno_id=tipo_eno_evento.id,
                        nombre=evento_nombre,
                        grupo_id=grupo_id,
                        grupo_nombre=grupo_nombre,
                        clasificaciones=None,  # Usar las del grupo
                        estrategia=None,
                        total_casos=total_casos,
                        casos_confirmados=casos_confirmados,
                        casos_sospechosos=casos_sospechosos,
                        ultimo_caso=ultimo_caso.isoformat() if ultimo_caso else None,
                    )
                    eventos.append(evento)
        else:
            # Evento simple
            tipo_eno = (
                self.session.query(TipoEno)
                .filter(TipoEno.nombre == grupo_nombre)
                .first()
            )
            if tipo_eno:
                # Obtener estadísticas básicas del evento simple
                total_query = self.session.query(func.count(Evento.id)).filter(
                    Evento.id_tipo_eno == tipo_eno.id
                )
                total_casos = total_query.scalar() or 0

                confirmados_query = self.session.query(func.count(Evento.id)).filter(
                    Evento.id_tipo_eno == tipo_eno.id,
                    Evento.clasificacion_estrategia == "confirmados",
                )
                casos_confirmados = confirmados_query.scalar() or 0

                sospechosos_query = self.session.query(func.count(Evento.id)).filter(
                    Evento.id_tipo_eno == tipo_eno.id,
                    Evento.clasificacion_estrategia == "sospechosos",
                )
                casos_sospechosos = sospechosos_query.scalar() or 0

                ultimo_caso_query = self.session.query(
                    func.max(Evento.fecha_minima_evento)
                ).filter(Evento.id_tipo_eno == tipo_eno.id)
                ultimo_caso = ultimo_caso_query.scalar()

                evento = EventoDentroGrupo(
                    id=tipo_eno.id,
                    tipo_eno_id=tipo_eno.id,
                    nombre=grupo_nombre,
                    grupo_id=grupo_id,
                    grupo_nombre=grupo_nombre,
                    clasificaciones=grupo_config["clasificaciones"],
                    estrategia=None,
                    total_casos=total_casos,
                    casos_confirmados=casos_confirmados,
                    casos_sospechosos=casos_sospechosos,
                    ultimo_caso=ultimo_caso.isoformat() if ultimo_caso else None,
                )
                eventos.append(evento)

        # Filtrar gráficos disponibles
        graficos_disponibles = [
            grafico
            for grafico in self.graficos_config
            if grafico.disponible_para_todos
            or grupo_nombre in grafico.disponible_para_grupos
        ]

        return GrupoEventoResponse(
            grupo=grupo, eventos=eventos, graficos_disponibles=graficos_disponibles
        )

    async def get_datos_visualizacion(
        self, request: DatosVisualizacionRequest
    ) -> DatosVisualizacionResponse:
        """Obtiene datos para una visualización específica."""

        # Obtener información del grupo
        grupo_detalle = await self.get_grupo_detalle(request.grupo_id)
        if not grupo_detalle:
            raise ValueError(f"Grupo {request.grupo_id} no encontrado")

        # IDs de eventos a incluir
        evento_ids = (
            request.evento_ids
            if request.evento_ids
            else [e.tipo_eno_id for e in grupo_detalle.eventos]
        )

        # Query base
        query = self.session.query(Evento).filter(Evento.id_tipo_eno.in_(evento_ids))

        # Aplicar filtros
        filtros_aplicados = {}

        if request.clasificacion != "todos":
            query = query.filter(
                Evento.clasificacion_estrategia == request.clasificacion
            )
            filtros_aplicados["clasificacion"] = request.clasificacion

        if request.fecha_desde:
            fecha_desde = datetime.strptime(request.fecha_desde, "%Y-%m-%d").date()
            query = query.filter(Evento.fecha_minima_evento >= fecha_desde)
            filtros_aplicados["fecha_desde"] = request.fecha_desde

        if request.fecha_hasta:
            fecha_hasta = datetime.strptime(request.fecha_hasta, "%Y-%m-%d").date()
            query = query.filter(Evento.fecha_minima_evento <= fecha_hasta)
            filtros_aplicados["fecha_hasta"] = request.fecha_hasta

        # Generar datos según tipo de gráfico
        datos = await self._generar_datos_grafico(query, request.tipo_grafico)

        # Contar total de casos
        total_casos = query.count()

        return DatosVisualizacionResponse(
            grupo=grupo_detalle.grupo.nombre,
            eventos=[
                e.nombre for e in grupo_detalle.eventos if e.tipo_eno_id in evento_ids
            ],
            clasificacion=request.clasificacion,
            tipo_grafico=request.tipo_grafico,
            datos=datos,
            metadatos={
                "generated_at": datetime.now().isoformat(),
                "query_params": request.parametros_extra,
            },
            total_casos=total_casos,
            fecha_generacion=datetime.now().isoformat(),
            filtros_aplicados=filtros_aplicados,
        )

    async def _generar_datos_grafico(
        self, query, tipo_grafico: str
    ) -> List[Dict[str, Any]]:
        """Genera datos específicos según el tipo de gráfico."""

        if tipo_grafico == "casos_por_edad":
            return await self._generar_casos_por_edad(query)
        elif tipo_grafico == "torta_sexo":
            return await self._generar_torta_sexo(query)
        elif tipo_grafico == "casos_mensual":
            return await self._generar_casos_mensual(query)
        elif tipo_grafico == "tabla":
            return await self._generar_tabla(query)
        else:
            # Gráfico genérico de totales
            return await self._generar_totales(query)

    async def _generar_casos_por_edad(self, query) -> List[Dict[str, Any]]:
        """Genera datos para gráfico de casos por edad."""
        # Unir con ciudadano para obtener fecha de nacimiento
        from app.domains.sujetos_epidemiologicos.ciudadanos_models.models import Ciudadano

        resultados = (
            query.join(Ciudadano)
            .with_entities(
                func.extract("year", func.age(Ciudadano.fecha_nacimiento)).label("edad")
            )
            .all()
        )

        # Agrupar por rangos etarios
        rangos = {
            "0-4": 0,
            "5-14": 0,
            "15-24": 0,
            "25-34": 0,
            "35-44": 0,
            "45-54": 0,
            "55-64": 0,
            "65+": 0,
            "Sin datos": 0,
        }

        for resultado in resultados:
            edad = resultado.edad
            if edad is None:
                rangos["Sin datos"] += 1
            elif edad < 5:
                rangos["0-4"] += 1
            elif edad < 15:
                rangos["5-14"] += 1
            elif edad < 25:
                rangos["15-24"] += 1
            elif edad < 35:
                rangos["25-34"] += 1
            elif edad < 45:
                rangos["35-44"] += 1
            elif edad < 55:
                rangos["45-54"] += 1
            elif edad < 65:
                rangos["55-64"] += 1
            else:
                rangos["65+"] += 1

        return [
            {"rango": rango, "casos": cantidad} for rango, cantidad in rangos.items()
        ]

    async def _generar_torta_sexo(self, query) -> List[Dict[str, Any]]:
        """Genera datos para gráfico de torta por sexo."""
        from app.domains.sujetos_epidemiologicos.ciudadanos_models.models import Ciudadano

        resultados = (
            query.join(Ciudadano)
            .with_entities(Ciudadano.sexo, func.count(Evento.id).label("casos"))
            .group_by(Ciudadano.sexo)
            .all()
        )

        return [{"sexo": r.sexo or "Sin datos", "casos": r.casos} for r in resultados]

    async def _generar_casos_mensual(self, query) -> List[Dict[str, Any]]:
        """Genera datos para gráfico mensual."""
        resultados = (
            query.with_entities(
                func.extract("year", Evento.fecha_minima_evento).label("anio"),
                func.extract("month", Evento.fecha_minima_evento).label("mes"),
                func.count(Evento.id).label("casos"),
            )
            .group_by("anio", "mes")
            .order_by("anio", "mes")
            .all()
        )

        return [
            {
                "periodo": f"{int(r.anio)}-{int(r.mes):02d}",
                "casos": r.casos,
                "anio": int(r.anio),
                "mes": int(r.mes),
            }
            for r in resultados
        ]

    async def _generar_tabla(self, query) -> List[Dict[str, Any]]:
        """Genera datos para tabla."""
        from app.domains.sujetos_epidemiologicos.ciudadanos_models.models import Ciudadano

        resultados = query.join(Ciudadano).limit(100).all()

        datos = []
        for evento in resultados:
            datos.append(
                {
                    "id": evento.id_evento_caso,
                    "nombre": f"{evento.ciudadano.nombre} {evento.ciudadano.apellido}",
                    "fecha": evento.fecha_minima_evento.isoformat()
                    if evento.fecha_minima_evento
                    else None,
                    "clasificacion": evento.clasificacion_estrategia,
                    "provincia": evento.ciudadano.provincia,
                    "localidad": evento.ciudadano.localidad,
                }
            )

        return datos

    async def _generar_totales(self, query) -> List[Dict[str, Any]]:
        """Genera datos de totales simples."""
        total = query.count()
        return [{"categoria": "Total de casos", "valor": total}]


# Instancia del servicio (será inyectada)
analytics_service = None


def get_analytics_service(session: Session) -> AnalyticsService:
    """Factory function para crear instancia del servicio."""
    return AnalyticsService(session)
