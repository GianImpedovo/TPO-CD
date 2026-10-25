"""Las 7 regiones turísticas de la EOH y qué provincias forman cada una.

Fuente: INDEC, "Encuesta de Ocupación Hotelera. Aspectos metodológicos" (Metodología N.º 34, 2020), punto 2.1.1.
La EVyTH ubica La Rioja en Norte; acá se usa la definición de la EOH (Cuyo) en todo el proyecto.
"""
REGIONES = ["Buenos Aires", "CABA", "Córdoba", "Cuyo", "Litoral", "Norte", "Patagonia"]
CODIGO_REGION = {r: i for i, r in enumerate(REGIONES, 1)}  # código numérico para el modelo de hotel

# código INDEC de provincia: (provincia, región)
PROVINCIAS = {
    2: ("Ciudad Autónoma de Buenos Aires", "CABA"),
    6: ("Buenos Aires", "Buenos Aires"),
    10: ("Catamarca", "Norte"),
    14: ("Córdoba", "Córdoba"),
    18: ("Corrientes", "Litoral"),
    22: ("Chaco", "Litoral"),
    26: ("Chubut", "Patagonia"),
    30: ("Entre Ríos", "Litoral"),
    34: ("Formosa", "Litoral"),
    38: ("Jujuy", "Norte"),
    42: ("La Pampa", "Patagonia"),
    46: ("La Rioja", "Cuyo"),
    50: ("Mendoza", "Cuyo"),
    54: ("Misiones", "Litoral"),
    58: ("Neuquén", "Patagonia"),
    62: ("Río Negro", "Patagonia"),
    66: ("Salta", "Norte"),
    70: ("San Juan", "Cuyo"),
    74: ("San Luis", "Cuyo"),
    78: ("Santa Cruz", "Patagonia"),
    82: ("Santa Fe", "Litoral"),
    86: ("Santiago del Estero", "Norte"),
    90: ("Tucumán", "Norte"),
    94: ("Tierra del Fuego", "Patagonia"),
}


def provincias_por_region():
    return {r: [p for p, reg in PROVINCIAS.values() if reg == r] for r in REGIONES}
