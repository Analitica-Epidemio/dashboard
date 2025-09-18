"""
Utilidad para generar códigos estables kebab-case y nombres capitalizados
para grupos y tipos ENO. Se usa en uploads y seeds para consistencia.
"""
import re
from typing import Optional


class CodigoGenerator:
    """Generador de códigos estables para grupos y tipos ENO"""
    
    @staticmethod
    def generar_codigo_kebab(nombre: str) -> str:
        """
        Genera código kebab-case estable desde nombre
        
        Args:
            nombre: Nombre del grupo/tipo (cualquier formato)
            
        Returns:
            Código en kebab-case estable entre environments
            
        Examples:
            "Dengue y Enfermedades Vectoriales" → "dengue-y-enfermedades-vectoriales"
            "INFECCIÓN RESPIRATORIA AGUDA" → "infeccion-respiratoria-aguda"
            "COVID-19" → "covid-19"
            "Rabia Animal (Murciélagos)" → "rabia-animal-murcielagos"
        """
        if not nombre or not isinstance(nombre, str):
            return "unknown"
        
        # 1. Normalizar texto
        texto = nombre.strip()
        
        # 2. Convertir a minúsculas
        texto = texto.lower()
        
        # 3. Remover acentos y caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
            'ñ': 'n', 'ç': 'c'
        }
        for accented, plain in replacements.items():
            texto = texto.replace(accented, plain)
        
        # 4. Remover paréntesis y contenido
        texto = re.sub(r'\([^)]*\)', '', texto)
        
        # 5. Reemplazar caracteres especiales y espacios por guiones
        texto = re.sub(r'[^\w\s-]', '', texto)  # Solo palabras, espacios y guiones
        texto = re.sub(r'[\s_]+', '-', texto)   # Espacios y underscores → guiones
        texto = re.sub(r'-+', '-', texto)       # Múltiples guiones → uno solo
        
        # 6. Limpiar bordes
        texto = texto.strip('-')
        
        # 7. Limitar longitud y asegurar que no esté vacío
        if not texto:
            return "unknown"
        
        return texto[:50]  # Max 50 caracteres
    
    @staticmethod
    def capitalizar_nombre(nombre: str) -> str:
        """
        Capitaliza correctamente nombres de grupos y tipos
        
        Args:
            nombre: Nombre en cualquier formato
            
        Returns:
            Nombre capitalizado correctamente
            
        Examples:
            "DENGUE Y ENFERMEDADES VECTORIALES" → "Dengue y Enfermedades Vectoriales"
            "infección respiratoria aguda" → "Infección Respiratoria Aguda"
            "covid-19" → "Covid-19"
        """
        if not nombre or not isinstance(nombre, str):
            return "Unknown"
        
        # 1. Normalizar espacios
        texto = re.sub(r'\s+', ' ', nombre.strip())
        
        # 2. Convertir a minúsculas primero
        texto = texto.lower()
        
        # 3. Capitalizar cada palabra, pero conservar artículos y preposiciones
        palabras_menores = {
            'y', 'e', 'o', 'u', 'de', 'del', 'la', 'el', 'los', 'las',
            'en', 'con', 'por', 'para', 'sin', 'sobre', 'tras', 'a'
        }
        
        palabras = texto.split()
        resultado = []
        
        for i, palabra in enumerate(palabras):
            # Siempre capitalizar primera y última palabra
            if i == 0 or i == len(palabras) - 1:
                resultado.append(palabra.capitalize())
            # Palabras menores en minúsculas (salvo al inicio/final)
            elif palabra in palabras_menores:
                resultado.append(palabra)
            # Resto en capitalize
            else:
                resultado.append(palabra.capitalize())
        
        # 4. Casos especiales (siglas, números)
        texto_final = ' '.join(resultado)
        
        # Preservar números con guiones
        texto_final = re.sub(r'\b(\w*\d+\w*)\b', lambda m: m.group(1).upper() if '-' in m.group(1) else m.group(1), texto_final)
        
        # Siglas conocidas
        siglas = ['COVID', 'VIH', 'SIDA', 'IRA', 'IRAG', 'ETI', 'ESI', 'VRS']
        for sigla in siglas:
            texto_final = re.sub(f'\\b{sigla.lower()}\\b', sigla, texto_final, flags=re.IGNORECASE)
        
        return texto_final
    
    @staticmethod
    def generar_par_grupo(nombre: str, descripcion: Optional[str] = None) -> dict:
        """
        Genera código y nombre para un grupo ENO
        
        Returns:
            Dict con código kebab-case y nombre capitalizado
        """
        return {
            "codigo": CodigoGenerator.generar_codigo_kebab(nombre),
            "nombre": CodigoGenerator.capitalizar_nombre(nombre),
            "descripcion": descripcion or f"Grupo {CodigoGenerator.capitalizar_nombre(nombre)}"
        }
    
    @staticmethod
    def generar_par_tipo(nombre: str, descripcion: Optional[str] = None) -> dict:
        """
        Genera código y nombre para un tipo ENO
        
        Returns:
            Dict con código kebab-case y nombre capitalizado
        """
        return {
            "codigo": CodigoGenerator.generar_codigo_kebab(nombre),
            "nombre": CodigoGenerator.capitalizar_nombre(nombre),
            "descripcion": descripcion or f"Tipo {CodigoGenerator.capitalizar_nombre(nombre)}"
        }


# Aliases para retrocompatibilidad
def generar_codigo_kebab(nombre: str) -> str:
    """Alias para CodigoGenerator.generar_codigo_kebab"""
    return CodigoGenerator.generar_codigo_kebab(nombre)

def capitalizar_nombre(nombre: str) -> str:
    """Alias para CodigoGenerator.capitalizar_nombre"""
    return CodigoGenerator.capitalizar_nombre(nombre)