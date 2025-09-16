"""
Utilidades para cálculos epidemiológicos
"""
from datetime import date, timedelta
from typing import Optional, Tuple


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