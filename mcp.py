"""
MCP Server para análisis turístico con Google Places API
Herramientas para mapeo de competencia y análisis de opiniones
"""
from fastmcp import FastMCP
from typing import Dict, List, Any

# Create server
mcp = FastMCP(
    name="Kay FastMCP",
    description=(
        "Servidor para el 'Agente Explorador'. Provee herramientas de "
        "inteligencia turística para el análisis de mercado, competencia "
        "y cadena de valor, siguiendo las buenas prácticas de SERNATUR."
    )
)


# Datos placeholder para desarrollo inicial
PLACEHOLDER_PLACES = {
    "tour astronómico": [
        {
            "place_id": "ChIJ123_astro_tour_elqui",
            "name": "Observatorio Cerro Mayu",
            "address": "Ruta 41, Vicuña, Valle del Elqui",
            "website": "https://cerromayu.cl",
            "rating": 4.5,
            "types": ["tourist_attraction", "night_club"],
            "category": "competencia_directa"
        },
        {
            "place_id": "ChIJ456_astro_center",
            "name": "Centro Astronómico Andino",
            "address": "Camino El Pangue, Pisco Elqui",
            "website": "https://astroandino.cl",
            "rating": 4.3,
            "types": ["tourist_attraction", "establishment"],
            "category": "competencia_directa"
        },
        {
            "place_id": "ChIJ789_museum_gabriela",
            "name": "Museo Gabriela Mistral",
            "address": "Gabriela Mistral 759, Vicuña",
            "website": "https://museogabrielamistral.cl",
            "rating": 4.2,
            "types": ["museum", "tourist_attraction"],
            "category": "competencia_indirecta"
        },
        {
            "place_id": "ChIJ101_hotel_elqui",
            "name": "Hotel Valle del Elqui",
            "address": "Av. Bernardo O'Higgins 542, Vicuña",
            "website": "https://hotelvalleelqui.cl",
            "rating": 4.0,
            "types": ["lodging", "establishment"],
            "category": "colaboradores_potenciales"
        },
        {
            "place_id": "ChIJ202_restaurant_solar",
            "name": "Restaurant Solar de Baviera",
            "address": "Av. Bernardo O'Higgins 274, Vicuña",
            "website": "https://solardebaviera.cl",
            "rating": 4.4,
            "types": ["restaurant", "food"],
            "category": "colaboradores_potenciales"
        }
    ]
}

PLACEHOLDER_REVIEWS = {
    "ChIJ123_astro_tour_elqui": {
        "reviews": [
            {
                "author_name": "María González",
                "rating": 5,
                "text": "Increíble experiencia astronómica. El guía fue muy conocedor y el equipo excelente. Vale la pena el viaje al Valle del Elqui solo por esto.",
                "time": "2024-08-15"
            },
            {
                "author_name": "Carlos Rojas",
                "rating": 4,
                "text": "Muy buena actividad, aunque un poco cara. Los telescopios son profesionales y se aprende mucho. Llevar ropa abrigada porque hace frío en la noche.",
                "time": "2024-07-22"
            },
            {
                "author_name": "Ana Pérez",
                "rating": 5,
                "text": "Perfecto para ir en familia. Los niños quedaron fascinados viendo Saturno y Júpiter. El guía explicó todo de manera muy didáctica.",
                "time": "2024-06-10"
            },
            {
                "author_name": "Pedro Silva",
                "rating": 3,
                "text": "La experiencia estuvo bien, pero esperaba ver más cosas. El precio me pareció un poco elevado para lo que ofrecen. El equipo sí es bueno.",
                "time": "2024-05-18"
            }
        ]
    }
}

def clasificar_lugares(places: List[Dict], query: str) -> Dict[str, List[Dict]]:
    """
    Clasifica lugares en categorías para análisis de competencia
    """
    clasificados = {
        "competencia_directa": [],
        "competencia_indirecta": [],
        "colaboradores_potenciales": []
    }
    
    for place in places:
        types = place.get("types", [])
        name_lower = place.get("name", "").lower()
        query_lower = query.lower()
        
        # Lógica de clasificación basada en tipos y nombres
        if any(t in ["tourist_attraction", "travel_agency"] for t in types):
            if any(keyword in name_lower for keyword in ["observatorio", "astronómico", "astro", "tour"]):
                if query_lower in name_lower or any(q in name_lower for q in query_lower.split()):
                    place["category"] = "competencia_directa"
                    clasificados["competencia_directa"].append(place)
                else:
                    place["category"] = "competencia_indirecta"
                    clasificados["competencia_indirecta"].append(place)
            else:
                place["category"] = "competencia_indirecta"
                clasificados["competencia_indirecta"].append(place)
        elif any(t in ["lodging", "restaurant", "food", "store"] for t in types):
            place["category"] = "colaboradores_potenciales"
            clasificados["colaboradores_potenciales"].append(place)
        else:
            place["category"] = "competencia_indirecta"
            clasificados["competencia_indirecta"].append(place)
    
    return clasificados

def analizar_sentimiento_simple(texto: str) -> str:
    """
    Análisis de sentimiento básico basado en palabras clave
    """
    palabras_positivas = ["excelente", "increíble", "perfecto", "bueno", "recomiendo", "fascinante", "vale la pena"]
    palabras_negativas = ["malo", "terrible", "caro", "frío", "elevado", "esperaba más"]
    
    texto_lower = texto.lower()
    pos_count = sum(1 for palabra in palabras_positivas if palabra in texto_lower)
    neg_count = sum(1 for palabra in palabras_negativas if palabra in texto_lower)
    
    if pos_count > neg_count:
        return "positivo"
    elif neg_count > pos_count:
        return "negativo"
    else:
        return "neutro"

@mcp.tool()
def mapeo_competencia_y_colaboradores(
    query: str, 
    ubicacion: str, 
    radio_km: int = 50
) -> Dict[str, Any]:
    """
    Realiza búsquedas geolocalizadas para encontrar actores turísticos y los clasifica
    en competencia directa, indirecta y colaboradores potenciales.
    
    Args:
        query: Tipo de negocio o actividad a buscar (ej: "tour astronómico")
        ubicacion: Ubicación donde buscar (ej: "Valle del Elqui")
        radio_km: Radio de búsqueda en kilómetros (default: 50)
    
    Returns:
        Objeto JSON con actores clasificados incluyendo nombre, dirección, 
        website y place_id de cada lugar encontrado.
    """
    
    # Por ahora usamos datos placeholder
    # TODO: Integrar con Google Places API
    
    places_data = PLACEHOLDER_PLACES.get(query.lower(), [])
    
    if not places_data:
        # Generar datos de ejemplo si no hay coincidencias exactas
        places_data = [
            {
                "place_id": f"placeholder_{hash(query + ubicacion) % 10000}",
                "name": f"Negocio relacionado con {query}",
                "address": f"Dirección en {ubicacion}",
                "website": "https://ejemplo.cl",
                "rating": 4.0,
                "types": ["establishment"],
                "category": "competencia_indirecta"
            }
        ]
    
    # Clasificar los lugares encontrados
    clasificados = clasificar_lugares(places_data, query)
    
    resultado = {
        "query": query,
        "ubicacion": ubicacion,
        "radio_km": radio_km,
        "total_encontrados": len(places_data),
        "clasificacion": clasificados,
        "resumen": {
            "competencia_directa": len(clasificados["competencia_directa"]),
            "competencia_indirecta": len(clasificados["competencia_indirecta"]),
            "colaboradores_potenciales": len(clasificados["colaboradores_potenciales"])
        }
    }
    
    return resultado

@mcp.tool()
def analizador_de_opiniones(
    place_id: str, 
    idioma: str = "es"
) -> Dict[str, Any]:
    """
    Extrae y analiza reseñas de un lugar específico para identificar sentimientos,
    temas recurrentes, fortalezas y debilidades.
    
    Args:
        place_id: ID del lugar obtenido de Google Places (de la herramienta 1)
        idioma: Idioma de las reseñas a analizar (default: "es")
    
    Returns:
        Resumen estructurado con análisis de sentimientos, fortalezas, 
        debilidades y temas principales extraídos de las reseñas.
    """
    
    # Por ahora usamos datos placeholder
    # TODO: Integrar con Google Places Details API
    
    reviews_data = PLACEHOLDER_REVIEWS.get(place_id, {"reviews": []})
    reviews = reviews_data["reviews"]
    
    if not reviews:
        return {
            "place_id": place_id,
            "error": "No se encontraron reseñas para este lugar",
            "total_reviews": 0
        }
    
    # Análisis de sentimientos
    sentimientos = [analizar_sentimiento_simple(review["text"]) for review in reviews]
    sentimiento_counts = {
        "positivo": sentimientos.count("positivo"),
        "negativo": sentimientos.count("negativo"),
        "neutro": sentimientos.count("neutro")
    }
    
    # Extracción de temas recurrentes (keywords)
    temas_keywords = {
        "guía": 0, "precio": 0, "niños": 0, "frío": 0, "equipo": 0,
        "telescopio": 0, "experiencia": 0, "familia": 0, "caro": 0,
        "profesional": 0, "didáctico": 0, "conocedor": 0
    }
    
    fortalezas = []
    debilidades = []
    
    for review in reviews:
        texto_lower = review["text"].lower()
        
        # Contar keywords
        for keyword in temas_keywords:
            if keyword in texto_lower:
                temas_keywords[keyword] += 1
        
        # Extraer fortalezas y debilidades basado en sentimiento y rating
        if review["rating"] >= 4:
            if "excelente" in texto_lower or "increíble" in texto_lower or "perfecto" in texto_lower:
                fortalezas.append({
                    "frase": review["text"][:100] + "..." if len(review["text"]) > 100 else review["text"],
                    "rating": review["rating"],
                    "aspecto": "experiencia_general"
                })
        elif review["rating"] <= 3:
            if "caro" in texto_lower or "elevado" in texto_lower or "esperaba" in texto_lower:
                debilidades.append({
                    "frase": review["text"][:100] + "..." if len(review["text"]) > 100 else review["text"],
                    "rating": review["rating"],
                    "aspecto": "precio_expectativas"
                })
    
    # Calcular rating promedio
    rating_promedio = sum(review["rating"] for review in reviews) / len(reviews)
    
    # Temas principales (top 5)
    temas_principales = sorted(
        [(tema, count) for tema, count in temas_keywords.items() if count > 0],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    resultado = {
        "place_id": place_id,
        "idioma": idioma,
        "total_reviews": len(reviews),
        "rating_promedio": round(rating_promedio, 1),
        "sentimiento_general": {
            "distribucion": sentimiento_counts,
            "predominante": max(sentimiento_counts, key=sentimiento_counts.get)
        },
        "temas_principales": [{"tema": tema, "menciones": count} for tema, count in temas_principales],
        "fortalezas": fortalezas[:3],  # Top 3 fortalezas
        "debilidades": debilidades[:3],  # Top 3 debilidades
        "insights": {
            "precio_mencionado": temas_keywords["precio"] + temas_keywords["caro"] > 0,
            "apto_familias": temas_keywords["niños"] + temas_keywords["familia"] > 0,
            "calidad_guia": temas_keywords["guía"] + temas_keywords["conocedor"] + temas_keywords["didáctico"] > 0,
            "calidad_equipo": temas_keywords["equipo"] + temas_keywords["telescopio"] + temas_keywords["profesional"] > 0
        }
    }
    
    return resultado
