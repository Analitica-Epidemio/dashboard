"""
Generador de slugs y nombres normalizados.

Funciones para generar slugs estables (kebab-case) y nombres capitalizados.
Se usa en uploads, seeds y cualquier lugar donde se necesite un identificador
URL-friendly y estable.
"""
import re


def generar_slug(nombre: str) -> str:
    """
    Genera un slug kebab-case estable desde un nombre.

    Args:
        nombre: Nombre en cualquier formato

    Returns:
        Slug en kebab-case (max 50 caracteres)

    Examples:
        >>> generar_slug("Dengue")
        'dengue'
        >>> generar_slug("Rabia Humana")
        'rabia-humana'
        >>> generar_slug("INFECCIÓN RESPIRATORIA AGUDA")
        'infeccion-respiratoria-aguda'
        >>> generar_slug("COVID-19")
        'covid-19'
    """
    if not nombre or not isinstance(nombre, str):
        return "unknown"

    texto = nombre.strip().lower()

    # Remover acentos
    acentos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    for acento, plain in acentos.items():
        texto = texto.replace(acento, plain)

    # Remover paréntesis y contenido
    texto = re.sub(r'\([^)]*\)', '', texto)

    # Solo letras, números, espacios y guiones
    texto = re.sub(r'[^\w\s-]', '', texto)
    texto = re.sub(r'[\s_]+', '-', texto)
    texto = re.sub(r'-+', '-', texto)
    texto = texto.strip('-')

    return texto[:50] if texto else "unknown"


def capitalizar_nombre(nombre: str) -> str:
    """
    Capitaliza correctamente un nombre, respetando artículos y siglas.

    Args:
        nombre: Nombre en cualquier formato

    Returns:
        Nombre capitalizado

    Examples:
        >>> capitalizar_nombre("DENGUE")
        'Dengue'
        >>> capitalizar_nombre("infección respiratoria aguda")
        'Infección Respiratoria Aguda'
    """
    if not nombre or not isinstance(nombre, str):
        return "Unknown"

    texto = re.sub(r'\s+', ' ', nombre.strip()).lower()

    palabras_menores = {
        'y', 'e', 'o', 'u', 'de', 'del', 'la', 'el', 'los', 'las',
        'en', 'con', 'por', 'para', 'sin', 'sobre', 'tras', 'a'
    }

    palabras = texto.split()
    resultado = []

    for i, palabra in enumerate(palabras):
        if i == 0 or i == len(palabras) - 1:
            resultado.append(palabra.capitalize())
        elif palabra in palabras_menores:
            resultado.append(palabra)
        else:
            resultado.append(palabra.capitalize())

    texto_final = ' '.join(resultado)

    # Siglas conocidas
    for sigla in ['COVID', 'VIH', 'SIDA', 'IRA', 'IRAG', 'ETI', 'ESI', 'VSR']:
        texto_final = re.sub(
            f'\\b{sigla.lower()}\\b',
            sigla,
            texto_final,
            flags=re.IGNORECASE
        )

    return texto_final
