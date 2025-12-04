"""
Utilidades para cálculo de períodos epidemiológicos
"""

from datetime import date, timedelta
from typing import Tuple

from app.api.v1.analytics.schemas import PeriodInfo, PeriodType


def get_epi_week(fecha: date) -> Tuple[int, int]:
    """
    Calcula la semana epidemiológica (ISO week) de una fecha.
    Retorna (año_epi, semana_epi)
    """
    iso_calendar = fecha.isocalendar()
    return iso_calendar[0], iso_calendar[1]


def get_epi_week_dates(semana: int, anio: int) -> Tuple[date, date]:
    """
    Calcula las fechas de inicio y fin de una semana epidemiológica.

    Args:
        semana: Número de semana epidemiológica (1-53)
        anio: Año epidemiológico

    Returns:
        Tupla (fecha_inicio, fecha_fin) - Lunes a Domingo de esa semana
    """
    # Crear fecha del primer día del año
    primer_dia = date(anio, 1, 1)

    # Encontrar el lunes de la semana 1 del año ISO
    # ISO week 1 es la primera semana que tiene jueves
    iso_cal = primer_dia.isocalendar()
    dias_hasta_lunes_semana1 = (1 - primer_dia.weekday()) % 7
    if iso_cal[1] > 1:
        # Si el 1 de enero no está en semana 1, ajustar
        dias_hasta_lunes_semana1 += 7

    lunes_semana1 = primer_dia + timedelta(days=dias_hasta_lunes_semana1)

    # Calcular lunes de la semana objetivo
    lunes_objetivo = lunes_semana1 + timedelta(weeks=(semana - 1))
    domingo_objetivo = lunes_objetivo + timedelta(days=6)

    return lunes_objetivo, domingo_objetivo


def get_period_dates(
    period_type: PeriodType,
    fecha_referencia: date | None = None
) -> Tuple[date, date]:
    """
    Calcula las fechas de inicio y fin de un período predefinido.

    Args:
        period_type: Tipo de período a calcular
        fecha_referencia: Fecha de referencia para cálculos (default: hoy).
                         Esta fecha actúa como "hoy" en el contexto del análisis,
                         permitiendo "viajar en el tiempo" para ver métricas históricas.

    Returns:
        Tupla (fecha_desde, fecha_hasta)
    """
    if fecha_referencia is None:
        fecha_referencia = date.today()

    if period_type == PeriodType.ULTIMA_SEMANA_EPI:
        # Última semana epidemiológica completa (lunes a domingo)
        # Buscar el lunes de la semana actual
        dias_desde_lunes = fecha_referencia.weekday()  # 0 = lunes
        lunes_actual = fecha_referencia - timedelta(days=dias_desde_lunes)
        # Ir a la semana anterior
        fecha_hasta = lunes_actual - timedelta(days=1)  # Domingo de semana anterior
        fecha_desde = fecha_hasta - timedelta(days=6)  # Lunes de semana anterior

    elif period_type == PeriodType.ULTIMAS_4_SEMANAS_EPI:
        # Últimas 4 semanas epidemiológicas completas
        dias_desde_lunes = fecha_referencia.weekday()
        lunes_actual = fecha_referencia - timedelta(days=dias_desde_lunes)
        fecha_hasta = lunes_actual - timedelta(days=1)  # Domingo de semana anterior
        fecha_desde = fecha_hasta - timedelta(days=27)  # 4 semanas = 28 días - 1

    elif period_type == PeriodType.ULTIMAS_12_SEMANAS_EPI:
        # Últimas 12 semanas epidemiológicas completas
        dias_desde_lunes = fecha_referencia.weekday()
        lunes_actual = fecha_referencia - timedelta(days=dias_desde_lunes)
        fecha_hasta = lunes_actual - timedelta(days=1)  # Domingo de semana anterior
        fecha_desde = fecha_hasta - timedelta(days=83)  # 12 semanas = 84 días - 1

    elif period_type == PeriodType.MES_HASTA_FECHA:
        # Del día 1 del mes actual hasta hoy
        fecha_desde = date(fecha_referencia.year, fecha_referencia.month, 1)
        fecha_hasta = fecha_referencia

    elif period_type == PeriodType.MES_PASADO:
        # Mes anterior completo
        primer_dia_mes_actual = date(fecha_referencia.year, fecha_referencia.month, 1)
        fecha_hasta = primer_dia_mes_actual - timedelta(days=1)  # Último día mes anterior
        fecha_desde = date(fecha_hasta.year, fecha_hasta.month, 1)

    elif period_type == PeriodType.ULTIMOS_3_MESES:
        # Últimos 3 meses completos
        fecha_hasta = fecha_referencia
        fecha_desde = fecha_referencia - timedelta(days=90)

    elif period_type == PeriodType.TRIMESTRE_ACTUAL:
        # Trimestre actual hasta la fecha
        mes_inicio_trimestre = ((fecha_referencia.month - 1) // 3) * 3 + 1
        fecha_desde = date(fecha_referencia.year, mes_inicio_trimestre, 1)
        fecha_hasta = fecha_referencia

    elif period_type == PeriodType.TRIMESTRE_PASADO:
        # Trimestre anterior completo
        mes_inicio_trimestre_actual = ((fecha_referencia.month - 1) // 3) * 3 + 1
        primer_dia_trimestre_actual = date(fecha_referencia.year, mes_inicio_trimestre_actual, 1)
        fecha_hasta = primer_dia_trimestre_actual - timedelta(days=1)
        mes_inicio_trimestre_anterior = ((fecha_hasta.month - 1) // 3) * 3 + 1
        fecha_desde = date(fecha_hasta.year, mes_inicio_trimestre_anterior, 1)

    elif period_type == PeriodType.ULTIMOS_6_MESES:
        # Últimos 6 meses
        fecha_hasta = fecha_referencia
        fecha_desde = fecha_referencia - timedelta(days=180)

    elif period_type == PeriodType.ANIO_HASTA_FECHA:
        # Del 1 de enero hasta hoy
        fecha_desde = date(fecha_referencia.year, 1, 1)
        fecha_hasta = fecha_referencia

    elif period_type == PeriodType.ANIO_PASADO:
        # Año anterior completo
        fecha_desde = date(fecha_referencia.year - 1, 1, 1)
        fecha_hasta = date(fecha_referencia.year - 1, 12, 31)

    else:
        # PERSONALIZADO - no aplica aquí
        raise ValueError("Período personalizado debe especificar fechas explícitamente")

    return fecha_desde, fecha_hasta


def get_comparison_period(
    fecha_desde: date,
    fecha_hasta: date,
    comparison_type: str
) -> Tuple[date, date]:
    """
    Calcula el período de comparación basado en el período actual.

    Args:
        fecha_desde: Fecha inicio del período actual
        fecha_hasta: Fecha fin del período actual
        comparison_type: "rolling" o "year_over_year"

    Returns:
        Tupla (fecha_desde_comp, fecha_hasta_comp)
    """
    duracion_dias = (fecha_hasta - fecha_desde).days + 1

    if comparison_type == "rolling":
        # Período anterior del mismo tamaño
        fecha_hasta_comp = fecha_desde - timedelta(days=1)
        fecha_desde_comp = fecha_hasta_comp - timedelta(days=duracion_dias - 1)

    elif comparison_type == "year_over_year":
        # Mismo período del año anterior
        fecha_desde_comp = date(fecha_desde.year - 1, fecha_desde.month, fecha_desde.day)
        fecha_hasta_comp = date(fecha_hasta.year - 1, fecha_hasta.month, fecha_hasta.day)

    else:
        raise ValueError(f"Tipo de comparación inválido: {comparison_type}")

    return fecha_desde_comp, fecha_hasta_comp


def create_period_info(
    fecha_desde: date,
    fecha_hasta: date,
    descripcion: str
) -> PeriodInfo:
    """
    Crea un objeto PeriodInfo con las semanas epidemiológicas calculadas.
    """
    anio_desde, semana_desde = get_epi_week(fecha_desde)
    anio_hasta, semana_hasta = get_epi_week(fecha_hasta)

    # Si el período cruza años, usar el año predominante
    anio_epi = anio_hasta if (fecha_hasta - fecha_desde).days >= 180 else anio_desde

    return PeriodInfo(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        semana_epi_desde=semana_desde,
        semana_epi_hasta=semana_hasta,
        anio_epi=anio_epi,
        descripcion=descripcion
    )


def get_period_description(period_type: PeriodType, fecha_desde: date, fecha_hasta: date) -> str:
    """
    Genera una descripción legible del período.
    """
    descriptions = {
        PeriodType.ULTIMA_SEMANA_EPI: f"Última semana epi ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ULTIMAS_4_SEMANAS_EPI: f"Últimas 4 semanas epi ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ULTIMAS_12_SEMANAS_EPI: f"Últimas 12 semanas epi ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.MES_HASTA_FECHA: f"Mes hasta la fecha ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.MES_PASADO: f"Mes pasado ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ULTIMOS_3_MESES: f"Últimos 3 meses ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.TRIMESTRE_ACTUAL: f"Trimestre actual ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.TRIMESTRE_PASADO: f"Trimestre pasado ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ULTIMOS_6_MESES: f"Últimos 6 meses ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ANIO_HASTA_FECHA: f"Año hasta la fecha ({fecha_desde.strftime('%d/%m')} - {fecha_hasta.strftime('%d/%m')})",
        PeriodType.ANIO_PASADO: f"Año {fecha_desde.year}",
        PeriodType.PERSONALIZADO: f"{fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}",
    }

    return descriptions.get(period_type, f"{fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}")
