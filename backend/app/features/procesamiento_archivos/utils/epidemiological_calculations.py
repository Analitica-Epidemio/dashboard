"""
Utilidades para cálculos epidemiológicos
"""
from datetime import date, timedelta
from typing import Dict, Optional, Tuple


def calcular_semana_epidemiologica(fecha: date) -> Tuple[int, int]:
    """
    Calcula la semana epidemiológica y el año epidemiológico para una fecha dada.

    Las semanas epidemiológicas:
    - Comienzan el domingo y terminan el sábado
    - La semana 1 es la primera semana del año que tiene al menos 4 días en el nuevo año
    - Si el 1 de enero es domingo, lunes, martes o miércoles, es semana 1
    - Si el 1 de enero es jueves, viernes o sábado, pertenece a la última semana del año anterior

    Args:
        fecha: Fecha para calcular

    Returns:
        Tupla (semana_epidemiologica, año_epidemiologico)
    """
    if not fecha:
        return None, None

    # Encontrar el primer día del año
    primer_dia_año = date(fecha.year, 1, 1)

    # Encontrar el primer domingo del año (o el 1 de enero si es domingo)
    dias_hasta_domingo = (6 - primer_dia_año.weekday()) % 7
    primer_domingo = primer_dia_año + timedelta(days=dias_hasta_domingo)

    # Si el primer domingo es después del 4 de enero, la semana 1 comienza el domingo anterior
    if primer_domingo.day > 4:
        primer_domingo -= timedelta(days=7)

    # Calcular el número de semana
    if fecha < primer_domingo:
        # La fecha pertenece a la última semana del año anterior
        año_anterior = fecha.year - 1
        primer_dia_año_anterior = date(año_anterior, 1, 1)
        dias_hasta_domingo = (6 - primer_dia_año_anterior.weekday()) % 7
        primer_domingo_anterior = primer_dia_año_anterior + timedelta(days=dias_hasta_domingo)
        if primer_domingo_anterior.day > 4:
            primer_domingo_anterior -= timedelta(days=7)

        # Calcular cuántas semanas hay en el año anterior
        ultimo_dia_año_anterior = date(año_anterior, 12, 31)
        dias_transcurridos = (ultimo_dia_año_anterior - primer_domingo_anterior).days
        semanas_año_anterior = (dias_transcurridos // 7) + 1

        return semanas_año_anterior, año_anterior
    else:
        # Calcular la semana dentro del año actual
        dias_transcurridos = (fecha - primer_domingo).days
        semana = (dias_transcurridos // 7) + 1

        # Verificar si es la semana 53 que en realidad pertenece al próximo año
        if semana > 52:
            # Verificar si el próximo año ya comenzó
            ultimo_dia_año = date(fecha.year, 12, 31)
            dias_hasta_fin = (ultimo_dia_año - fecha).days
            if dias_hasta_fin < 3:  # Los últimos días pueden pertenecer a la semana 1 del próximo año
                primer_dia_proximo = date(fecha.year + 1, 1, 1)
                dias_hasta_domingo_proximo = (6 - primer_dia_proximo.weekday()) % 7
                primer_domingo_proximo = primer_dia_proximo + timedelta(days=dias_hasta_domingo_proximo)
                if primer_domingo_proximo.day > 4:
                    primer_domingo_proximo -= timedelta(days=7)

                if fecha >= primer_domingo_proximo - timedelta(days=7):
                    return 1, fecha.year + 1

        return semana, fecha.year


def calcular_edad(fecha_nacimiento: Optional[date], fecha_evento: date) -> Optional[int]:
    """
    Calcula la edad en años completos entre fecha de nacimiento y fecha del evento.

    Args:
        fecha_nacimiento: Fecha de nacimiento
        fecha_evento: Fecha del evento

    Returns:
        Edad en años o None si no se puede calcular
    """
    if not fecha_nacimiento or not fecha_evento:
        return None

    edad = fecha_evento.year - fecha_nacimiento.year

    # Ajustar si aún no ha cumplido años este año
    if fecha_evento.month < fecha_nacimiento.month or \
       (fecha_evento.month == fecha_nacimiento.month and fecha_evento.day < fecha_nacimiento.day):
        edad -= 1

    return edad if edad >= 0 else None


def obtener_fechas_semana_epidemiologica(year: int, week: int) -> Tuple[date, date]:
    """
    Obtiene las fechas de inicio (domingo) y fin (sábado) para una semana epidemiológica dada.

    Esta es la función inversa de calcular_semana_epidemiologica().

    Args:
        year: Año epidemiológico
        week: Número de semana epidemiológica (1-52/53)

    Returns:
        Tupla (fecha_inicio_domingo, fecha_fin_sabado)
    """
    # Encontrar el primer día del año
    primer_dia_año = date(year, 1, 1)

    # Encontrar el primer domingo del año (o el 1 de enero si es domingo)
    dias_hasta_domingo = (6 - primer_dia_año.weekday()) % 7
    primer_domingo = primer_dia_año + timedelta(days=dias_hasta_domingo)

    # Si el primer domingo es después del 4 de enero, la semana 1 comienza el domingo anterior
    if primer_domingo.day > 4:
        primer_domingo -= timedelta(days=7)

    # Calcular la fecha de inicio de la semana solicitada
    fecha_inicio = primer_domingo + timedelta(weeks=week - 1)
    fecha_fin = fecha_inicio + timedelta(days=6)  # Sábado

    return fecha_inicio, fecha_fin


def generar_metadata_semanas(semana_inicio: int, año_inicio: int, semana_fin: int, año_fin: int) -> list[Dict]:
    """
    Genera metadata para un rango de semanas epidemiológicas.

    Args:
        semana_inicio: Semana epidemiológica de inicio
        año_inicio: Año epidemiológico de inicio
        semana_fin: Semana epidemiológica de fin
        año_fin: Año epidemiológico de fin

    Returns:
        Lista de diccionarios con metadata de cada semana
    """
    metadata = []

    # Caso simple: mismo año
    if año_inicio == año_fin:
        for week in range(semana_inicio, semana_fin + 1):
            start_date, end_date = obtener_fechas_semana_epidemiologica(año_inicio, week)
            metadata.append({
                "year": año_inicio,
                "week": week,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            })
    else:
        # Múltiples años: desde semana_inicio hasta fin del primer año
        # Determinar última semana del año_inicio
        ultima_semana_año_inicio = 52
        # Verificar si el año tiene semana 53
        try:
            obtener_fechas_semana_epidemiologica(año_inicio, 53)
            ultima_semana_año_inicio = 53
        except ValueError:
            pass

        # Semanas del primer año
        for week in range(semana_inicio, ultima_semana_año_inicio + 1):
            start_date, end_date = obtener_fechas_semana_epidemiologica(año_inicio, week)
            metadata.append({
                "year": año_inicio,
                "week": week,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            })

        # Años intermedios completos (si los hay)
        for year in range(año_inicio + 1, año_fin):
            ultima_semana = 52
            try:
                obtener_fechas_semana_epidemiologica(year, 53)
                ultima_semana = 53
            except ValueError:
                pass

            for week in range(1, ultima_semana + 1):
                start_date, end_date = obtener_fechas_semana_epidemiologica(year, week)
                metadata.append({
                    "year": year,
                    "week": week,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                })

        # Semanas del último año
        for week in range(1, semana_fin + 1):
            start_date, end_date = obtener_fechas_semana_epidemiologica(año_fin, week)
            metadata.append({
                "year": año_fin,
                "week": week,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            })

    return metadata
