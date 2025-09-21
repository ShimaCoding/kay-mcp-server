"""
MCP Server para análisis turístico con Google Places API
Herramientas para mapeo de competencia y análisis de opiniones
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import googlemaps
from fastmcp import FastMCP
from typing import Dict, List, Any
from dotenv import load_dotenv
from google_places_client import GooglePlacesClient, obtener_detalles_completos_de_lugar

# Cargar variables de entorno desde .env
load_dotenv()

# Create server
mcp = FastMCP(
    name="Kay FastMCP",
    instructions=(
        "Servidor para el 'Agente Explorador'. Provee herramientas de "
        "inteligencia turística para el análisis de mercado, competencia "
        "y cadena de valor, siguiendo las buenas prácticas de SERNATUR."
    )
)

# Configuración de caché
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)
GEOCODE_CACHE_FILE = CACHE_DIR / "geocode_cache.json"
PLACES_CACHE_FILE = CACHE_DIR / "places_cache.json"
REVIEWS_CACHE_FILE = CACHE_DIR / "reviews_cache.json"
PLACES_RAW_CACHE_FILE = CACHE_DIR / "places_raw_cache.json"
REVIEWS_RAW_CACHE_FILE = CACHE_DIR / "reviews_raw_cache.json"
CACHE_EXPIRY_HOURS = 24  # Los datos del caché expiran en 24 horas

def load_cache(cache_file: Path) -> Dict[str, Any]:
    """Carga el caché desde un archivo JSON"""
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_cache(cache_file: Path, cache_data: Dict[str, Any]) -> None:
    """Guarda el caché en un archivo JSON"""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: No se pudo guardar el caché: {e}")

def is_cache_valid(timestamp: str) -> bool:
    """Verifica si el caché sigue siendo válido"""
    try:
        cache_time = datetime.fromisoformat(timestamp)
        return datetime.now() - cache_time < timedelta(hours=CACHE_EXPIRY_HOURS)
    except (ValueError, TypeError):
        return False

def get_cache_key(query: str, ubicacion: str, radio_km: int) -> str:
    """Genera una clave única para el caché basada en los parámetros de búsqueda"""
    key_string = f"{query.lower()}_{ubicacion.lower()}_{radio_km}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_geocode_from_cache(ubicacion: str) -> Dict[str, Any]:
    """Obtiene resultado de geocodificación desde el caché"""
    cache = load_cache(GEOCODE_CACHE_FILE)
    ubicacion_key = ubicacion.lower()
    
    if ubicacion_key in cache:
        cached_data = cache[ubicacion_key]
        if is_cache_valid(cached_data.get("timestamp", "")):
            print(f"✓ Usando geocodificación de caché para: {ubicacion}")
            return cached_data.get("data", {})
    
    return {}

def save_geocode_to_cache(ubicacion: str, geocode_result: Dict[str, Any]) -> None:
    """Guarda resultado de geocodificación en el caché"""
    cache = load_cache(GEOCODE_CACHE_FILE)
    ubicacion_key = ubicacion.lower()
    
    cache[ubicacion_key] = {
        "data": geocode_result,
        "timestamp": datetime.now().isoformat()
    }
    
    save_cache(GEOCODE_CACHE_FILE, cache)
    print(f"✓ Geocodificación guardada en caché para: {ubicacion}")

def get_places_from_cache(query: str, ubicacion: str, radio_km: int) -> Dict[str, Any]:
    """Obtiene resultado de búsqueda de lugares desde el caché"""
    cache = load_cache(PLACES_CACHE_FILE)
    cache_key = get_cache_key(query, ubicacion, radio_km)
    
    if cache_key in cache:
        cached_data = cache[cache_key]
        if is_cache_valid(cached_data.get("timestamp", "")):
            print(f"✓ Usando búsqueda de lugares de caché para: {query} en {ubicacion}")
            return cached_data.get("data", {})
    
    return {}

def save_places_to_cache(query: str, ubicacion: str, radio_km: int, places_result: Dict[str, Any]) -> None:
    """Guarda resultado de búsqueda de lugares en el caché"""
    cache = load_cache(PLACES_CACHE_FILE)
    cache_key = get_cache_key(query, ubicacion, radio_km)
    
    cache[cache_key] = {
        "data": places_result,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "ubicacion": ubicacion,
        "radio_km": radio_km
    }
    
    save_cache(PLACES_CACHE_FILE, cache)
    print(f"✓ Búsqueda de lugares guardada en caché para: {query} en {ubicacion}")

def get_reviews_from_cache(place_id: str) -> Dict[str, Any]:
    """Obtiene análisis de reseñas desde el caché"""
    cache = load_cache(REVIEWS_CACHE_FILE)
    
    if place_id in cache:
        cached_data = cache[place_id]
        if is_cache_valid(cached_data.get("timestamp", "")):
            print(f"✓ Usando análisis de reseñas de caché para: {place_id}")
            return cached_data.get("data", {})
    
    return {}

def save_reviews_to_cache(place_id: str, reviews_result: Dict[str, Any]) -> None:
    """Guarda análisis de reseñas en el caché"""
    cache = load_cache(REVIEWS_CACHE_FILE)
    
    cache[place_id] = {
        "data": reviews_result,
        "timestamp": datetime.now().isoformat(),
        "place_id": place_id
    }
    
    save_cache(REVIEWS_CACHE_FILE, cache)
    print(f"✓ Análisis de reseñas guardado en caché para: {place_id}")

def get_places_raw_from_cache(query: str, ubicacion: str, radio_km: int) -> Dict[str, Any]:
    """Obtiene datos RAW de Google Places desde el caché"""
    cache = load_cache(PLACES_RAW_CACHE_FILE)
    cache_key = get_cache_key(query, ubicacion, radio_km)
    
    if cache_key in cache:
        cached_data = cache[cache_key]
        if is_cache_valid(cached_data.get("timestamp", "")):
            print(f"✓ Usando datos RAW de lugares de caché para: {query} en {ubicacion}")
            return cached_data.get("data", {})
    
    return {}

def save_places_raw_to_cache(query: str, ubicacion: str, radio_km: int, raw_data: Dict[str, Any]) -> None:
    """Guarda datos RAW de Google Places en el caché"""
    cache = load_cache(PLACES_RAW_CACHE_FILE)
    cache_key = get_cache_key(query, ubicacion, radio_km)
    
    cache[cache_key] = {
        "data": raw_data,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "ubicacion": ubicacion,
        "radio_km": radio_km,
        "api_source": "google_places_api"
    }
    
    save_cache(PLACES_RAW_CACHE_FILE, cache)
    print(f"✓ Datos RAW de lugares guardados en caché para: {query} en {ubicacion}")

def get_reviews_raw_from_cache(place_id: str) -> Dict[str, Any]:
    """Obtiene datos RAW de Google Places Details desde el caché"""
    cache = load_cache(REVIEWS_RAW_CACHE_FILE)
    
    if place_id in cache:
        cached_data = cache[place_id]
        if is_cache_valid(cached_data.get("timestamp", "")):
            print(f"✓ Usando datos RAW de reseñas de caché para: {place_id}")
            return cached_data.get("data", {})
    
    return {}

def save_reviews_raw_to_cache(place_id: str, raw_data: Dict[str, Any]) -> None:
    """Guarda datos RAW de Google Places Details en el caché"""
    cache = load_cache(REVIEWS_RAW_CACHE_FILE)
    
    cache[place_id] = {
        "data": raw_data,
        "timestamp": datetime.now().isoformat(),
        "place_id": place_id,
        "api_source": "google_places_details_api"
    }
    
    save_cache(REVIEWS_RAW_CACHE_FILE, cache)
    print(f"✓ Datos RAW de reseñas guardados en caché para: {place_id}")


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
    
    query_keywords = query.lower().split()
    
    for place in places:
        types = place.get("types", [])
        name_lower = place.get("name", "").lower()
        
        # Lógica de clasificación mejorada basada en tipos y nombres
        if any(t in ["tourist_attraction", "travel_agency", "point_of_interest"] for t in types):
            # Verificar si es competencia directa por keywords específicos
            if any(keyword in name_lower for keyword in ["observatorio", "astronomic", "astro", "tour", "observatory"]) or \
               any(q_word in name_lower for q_word in query_keywords):
                place["category"] = "competencia_directa"
                clasificados["competencia_directa"].append(place)
            else:
                place["category"] = "competencia_indirecta"
                clasificados["competencia_indirecta"].append(place)
        elif any(t in ["lodging", "hotel", "restaurant", "food", "bar", "store", "winery"] for t in types):
            place["category"] = "colaboradores_potenciales"
            clasificados["colaboradores_potenciales"].append(place)
        else:
            place["category"] = "competencia_indirecta"
            clasificados["competencia_indirecta"].append(place)
    
    return clasificados

def mapeo_competencia_y_colaboradores_placeholder(query: str, ubicacion: str, radio_km: int) -> Dict[str, Any]:
    """
    Función fallback que usa datos placeholder cuando falla la API
    """
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
        },
        "fuente": "datos_placeholder"
    }
    
    return resultado

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

def analizador_de_opiniones_placeholder(place_id: str) -> Dict[str, Any]:
    """
    Función fallback que usa datos placeholder cuando falla la API
    """
    reviews_data = PLACEHOLDER_REVIEWS.get(place_id, {"reviews": []})
    reviews = reviews_data["reviews"]
    
    if not reviews:
        return {
            "place_id": place_id,
            "error": "No se encontraron reseñas para este lugar",
            "total_reviews": 0,
            "fuente": "datos_placeholder"
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
    
    return {
        "place_id": place_id,
        "idioma": "es",
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
        },
        "fuente": "datos_placeholder"
    }

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
    
    # 1. Verificar configuración de API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"DEBUG: API Key detectada: {'Sí' if api_key else 'No'}")
    if api_key:
        print(f"DEBUG: API Key (primeros 10 chars): {api_key[:10]}...")
    
    if not api_key:
        print("WARNING: GOOGLE_API_KEY no configurada, usando datos placeholder")
        print("         Verifica que el archivo .env esté en el directorio correcto")
        return mapeo_competencia_y_colaboradores_placeholder(query, ubicacion, radio_km)
    
    # 2. Verificar caché de lugares primero
    cached_places_result = get_places_from_cache(query, ubicacion, radio_km)
    if cached_places_result:
        print('retornó el cache', cached_places_result)
        return cached_places_result
    
    try:
        # 3. Crear cliente de Google Maps
        gmaps = googlemaps.Client(key=api_key)

        # 4. Geocodificación con caché
        cached_geocode = get_geocode_from_cache(ubicacion)
        if cached_geocode:
            location = cached_geocode
        else:
            geocode_result = gmaps.geocode(address=ubicacion)
            if not geocode_result:
                print(f"WARNING: No se pudo geocodificar '{ubicacion}', usando datos placeholder")
                return mapeo_competencia_y_colaboradores_placeholder(query, ubicacion, radio_km)
            
            location = geocode_result[0]['geometry']['location']  # {'lat': ..., 'lng': ...}
            # Guardar en caché
            save_geocode_to_cache(ubicacion, location)

        # 5. Búsqueda de lugares usando Text Search
        places_result = gmaps.places(
            query=query,
            location=location,
            radius=radio_km * 1000  # La API usa metros
        )

        # 5.1. Guardar datos RAW completos de la API
        save_places_raw_to_cache(query, ubicacion, radio_km, places_result)

        google_places = places_result.get("results", [])
        print(f"✓ Encontrados {len(google_places)} lugares para '{query}' en '{ubicacion}'")
        # 6. Formatear datos para la función de clasificación
        formatted_places = []
        for place in google_places:
            formatted_place = {
                "place_id": place.get("place_id"),
                "name": place.get("name", "Nombre no disponible"),
                "address": place.get("vicinity", place.get("formatted_address", "Dirección no disponible")),
                "website": "No disponible",  # Requiere Places Details API para obtener website
                "rating": place.get("rating", "N/A"),
                "types": place.get("types", [])
            }
            formatted_places.append(formatted_place)

        # 7. Si no se encontraron lugares, usar fallback
        if not formatted_places:
            print(f"WARNING: No se encontraron lugares para '{query}' en '{ubicacion}', usando datos placeholder")
            return mapeo_competencia_y_colaboradores_placeholder(query, ubicacion, radio_km)

    except googlemaps.exceptions.ApiError as e:
        print(f"ERROR: API de Google Maps falló: {e}")
        return mapeo_competencia_y_colaboradores_placeholder(query, ubicacion, radio_km)
    except Exception as e:
        print(f"ERROR: Error inesperado: {e}")
        return mapeo_competencia_y_colaboradores_placeholder(query, ubicacion, radio_km)

    # 8. Clasificar los lugares encontrados
    clasificados = clasificar_lugares(formatted_places, query)
    
    resultado = {
        "query": query,
        "ubicacion": ubicacion,
        "radio_km": radio_km,
        "total_encontrados": len(formatted_places),
        "clasificacion": clasificados,
        "resumen": {
            "competencia_directa": len(clasificados["competencia_directa"]),
            "competencia_indirecta": len(clasificados["competencia_indirecta"]),
            "colaboradores_potenciales": len(clasificados["colaboradores_potenciales"])
        },
        "fuente": "google_places_api",
        "coordenadas_busqueda": {
            "lat": location['lat'],
            "lng": location['lng']
        }
    }
    
    # 9. Guardar resultado completo en caché
    save_places_to_cache(query, ubicacion, radio_km, resultado)
    
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
    
    # 1. Verificar configuración de API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"DEBUG: API Key detectada para reseñas: {'Sí' if api_key else 'No'}")
    
    if not api_key:
        print("WARNING: GOOGLE_API_KEY no configurada, usando datos placeholder para reseñas")
        return analizador_de_opiniones_placeholder(place_id)
    
    # 2. Verificar caché de reseñas procesadas primero
    cached_reviews_result = get_reviews_from_cache(place_id)
    
    # 3. Verificar si tenemos datos RAW, independientemente del caché procesado
    cached_raw_data = get_reviews_raw_from_cache(place_id)
    
    try:
        # 4. Si no tenemos datos RAW, hacer llamada a API
        if not cached_raw_data:
            # 4.1. Crear cliente de Google Maps
            gmaps = googlemaps.Client(key=api_key)
            
            # 4.2. Obtener detalles del lugar incluyendo reseñas
            place_details = gmaps.place(
                place_id=place_id,
                fields=['reviews', 'name', 'rating', 'user_ratings_total'],
                language=idioma
            )
            
            # 4.3. Guardar datos RAW completos de la API
            save_reviews_raw_to_cache(place_id, place_details)
            print(f"✓ Datos RAW obtenidos y guardados para: {place_id}")
        else:
            place_details = cached_raw_data
            print(f"✓ Usando datos RAW de caché para: {place_id}")
        
        # 5. Si ya tenemos análisis procesado, retornarlo
        if cached_reviews_result:
            print(f"✓ Retornando análisis procesado de caché para: {place_id}")
            return cached_reviews_result
        
        if 'result' not in place_details:
            print(f"WARNING: No se encontraron detalles para place_id {place_id}")
            return analizador_de_opiniones_placeholder(place_id)
        
        place_data = place_details['result']
        reviews = place_data.get('reviews', [])
        
        if not reviews:
            resultado = {
                "place_id": place_id,
                "error": "No se encontraron reseñas para este lugar",
                "total_reviews": 0,
                "fuente": "google_places_api"
            }
            # Guardar en caché incluso si no hay reseñas
            save_reviews_to_cache(place_id, resultado)
            return resultado
        
        print(f"✓ Encontradas {len(reviews)} reseñas para place_id: {place_id}")
        
    except googlemaps.exceptions.ApiError as e:
        print(f"ERROR: API de Google Maps falló para reseñas: {e}")
        return analizador_de_opiniones_placeholder(place_id)
    except Exception as e:
        print(f"ERROR: Error inesperado en análisis de reseñas: {e}")
        return analizador_de_opiniones_placeholder(place_id)
    
    # 5. Procesar reseñas de Google Places
    sentimientos = [analizar_sentimiento_simple(review.get("text", "")) for review in reviews]
    sentimiento_counts = {
        "positivo": sentimientos.count("positivo"),
        "negativo": sentimientos.count("negativo"),
        "neutro": sentimientos.count("neutro")
    }
    
    # 6. Extracción de temas recurrentes (keywords expandidos)
    temas_keywords = {
        "guía": 0, "precio": 0, "niños": 0, "frío": 0, "equipo": 0,
        "telescopio": 0, "experiencia": 0, "familia": 0, "caro": 0,
        "profesional": 0, "didáctico": 0, "conocedor": 0, "servicio": 0,
        "limpio": 0, "sucio": 0, "rápido": 0, "lento": 0, "amable": 0,
        "grosero": 0, "recomendado": 0, "no recomendado": 0
    }
    
    fortalezas = []
    debilidades = []
    
    for review in reviews:
        texto = review.get("text", "")
        rating = review.get("rating", 0)
        author = review.get("author_name", "Usuario anónimo")
        texto_lower = texto.lower()
        
        # Contar keywords
        for keyword in temas_keywords:
            if keyword in texto_lower:
                temas_keywords[keyword] += 1
        
        # Extraer fortalezas (rating >= 4)
        if rating >= 4:
            palabras_fortaleza = ["excelente", "increíble", "perfecto", "genial", "fantástico", "recomiendo"]
            if any(palabra in texto_lower for palabra in palabras_fortaleza):
                fortalezas.append({
                    "frase": texto[:120] + "..." if len(texto) > 120 else texto,
                    "rating": rating,
                    "autor": author,
                    "aspecto": "experiencia_general"
                })
        
        # Extraer debilidades (rating <= 3)
        elif rating <= 3:
            palabras_debilidad = ["caro", "elevado", "malo", "terrible", "no recomiendo", "esperaba más", "decepcionante"]
            if any(palabra in texto_lower for palabra in palabras_debilidad):
                debilidades.append({
                    "frase": texto[:120] + "..." if len(texto) > 120 else texto,
                    "rating": rating,
                    "autor": author,
                    "aspecto": "precio_expectativas" if any(p in texto_lower for p in ["caro", "elevado", "precio"]) else "experiencia_general"
                })
    
    # 7. Calcular métricas
    rating_promedio = place_data.get('rating', 0)
    total_ratings = place_data.get('user_ratings_total', 0)
    
    # 8. Temas principales (top 6)
    temas_principales = sorted(
        [(tema, count) for tema, count in temas_keywords.items() if count > 0],
        key=lambda x: x[1],
        reverse=True
    )[:6]
    
    # 9. Construir resultado
    resultado = {
        "place_id": place_id,
        "idioma": idioma,
        "nombre_lugar": place_data.get('name', 'Nombre no disponible'),
        "total_reviews": len(reviews),
        "total_ratings": total_ratings,
        "rating_promedio": rating_promedio,
        "sentimiento_general": {
            "distribucion": sentimiento_counts,
            "predominante": max(sentimiento_counts, key=sentimiento_counts.get) if sentimiento_counts else "neutro"
        },
        "temas_principales": [{"tema": tema, "menciones": count} for tema, count in temas_principales],
        "fortalezas": fortalezas[:4],  # Top 4 fortalezas
        "debilidades": debilidades[:4],  # Top 4 debilidades
        "insights": {
            "precio_mencionado": temas_keywords["precio"] + temas_keywords["caro"] > 0,
            "apto_familias": temas_keywords["niños"] + temas_keywords["familia"] > 0,
            "calidad_servicio": temas_keywords["servicio"] + temas_keywords["amable"] + temas_keywords["profesional"] > 0,
            "calidad_guia": temas_keywords["guía"] + temas_keywords["conocedor"] + temas_keywords["didáctico"] > 0,
            "calidad_equipo": temas_keywords["equipo"] + temas_keywords["telescopio"] + temas_keywords["profesional"] > 0,
            "limpieza_mencionada": temas_keywords["limpio"] + temas_keywords["sucio"] > 0,
            "velocidad_servicio": temas_keywords["rápido"] + temas_keywords["lento"] > 0
        },
        "fuente": "google_places_api",
        "fecha_analisis": datetime.now().isoformat()
    }
    
    # 10. Guardar resultado en caché
    save_reviews_to_cache(place_id, resultado)
    
    return resultado

@mcp.tool()
def obtener_detalles_lugar_v1(
    place_id: str
) -> Dict[str, Any]:
    """
    Obtiene detalles completos de un lugar específico usando la nueva API v1 de Google Places.
    Utiliza caché automático con hishel y guarda respaldos en archivos JSON.
    
    Args:
        place_id: ID único del lugar de Google Places (ej: "ChIJ123abc...")
    
    Returns:
        Diccionario con todos los detalles disponibles del lugar, incluyendo:
        - Información básica (nombre, dirección, teléfono, rating)
        - Horarios de funcionamiento
        - Fotos y reviews si están disponibles
        - Información de contacto completa
        - Metadatos de caché y fuente
    """
    
    # 1. Verificar configuración de API Key
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"DEBUG: API Key detectada para v1: {'Sí' if api_key else 'No'}")
    
    if not api_key:
        return {
            "place_id": place_id,
            "error": "GOOGLE_API_KEY no configurada",
            "message": "Verifica que el archivo .env esté en el directorio correcto",
            "fuente": "configuracion"
        }
    
    try:
        # 2. Usar el nuevo cliente GooglePlacesClient
        with GooglePlacesClient(api_key=api_key) as places_client:
            print(f"🔍 Obteniendo detalles para place_id: {place_id}")
            
            # 3. Obtener detalles completos (incluye guardado automático en JSON)
            resultado = obtener_detalles_completos_de_lugar(place_id, places_client)
            
            if resultado["status"] == "error":
                return {
                    "place_id": place_id,
                    "error": resultado["error"],
                    "error_code": resultado.get("error_code"),
                    "fuente": "google_places_api_v1"
                }
            
            # 4. Extraer datos principales para respuesta estructurada
            data = resultado["data"]
            
            # 5. Construir respuesta estructurada y amigable
            respuesta_estructurada = {
                "place_id": place_id,
                "status": "success",
                "fuente": "google_places_api_v1",
                "from_cache": resultado["from_cache"],
                "cache_status": "CACHE HIT" if resultado["from_cache"] else "API CALL",
                "timestamp": datetime.now().isoformat(),
                
                # Información básica
                "informacion_basica": {
                    "nombre": data.get("displayName", {}).get("text", "N/A"),
                    "direccion": data.get("formattedAddress", "N/A"),
                    "telefono_internacional": data.get("internationalPhoneNumber", "N/A"),
                    "telefono_nacional": data.get("nationalPhoneNumber", "N/A"),
                    "website": data.get("websiteUri", "N/A"),
                    "google_maps_uri": data.get("googleMapsUri", "N/A")
                },
                
                # Ratings y reviews
                "ratings": {
                    "rating_promedio": data.get("rating", "N/A"),
                    "total_reviews": data.get("userRatingCount", 0),
                    "nivel_precio": data.get("priceLevel", "N/A")
                },
                
                # Categorización
                "categoria": {
                    "tipos": data.get("types", []),
                    "categoria_principal": data.get("primaryType", "N/A"),
                    "estado_negocio": data.get("businessStatus", "N/A")
                },
                
                # Ubicación
                "ubicacion": {
                    "coordenadas": data.get("location", {}),
                    "viewport": data.get("viewport", {}),
                    "plus_code": data.get("plusCode", {})
                },
                
                # Horarios
                "horarios": {
                    "horarios_actuales": data.get("currentOpeningHours", {}),
                    "horarios_secundarios": data.get("currentSecondaryOpeningHours", []),
                    "abierto_ahora": data.get("currentOpeningHours", {}).get("openNow", "N/A")
                },
                
                # Información adicional
                "servicios": {
                    "delivery": data.get("delivery", "N/A"),
                    "dine_in": data.get("dineIn", "N/A"),
                    "takeout": data.get("takeout", "N/A"),
                    "reservable": data.get("reservable", "N/A"),
                    "serves_breakfast": data.get("servesBreakfast", "N/A"),
                    "serves_lunch": data.get("servesLunch", "N/A"),
                    "serves_dinner": data.get("servesDinner", "N/A"),
                    "serves_beer": data.get("servesBeer", "N/A"),
                    "serves_wine": data.get("servesWine", "N/A")
                },
                
                # Metadatos de la API
                "metadatos": {
                    "total_campos_disponibles": len(data.keys()),
                    "tiene_fotos": "photos" in data,
                    "tiene_reviews": "reviews" in data,
                    "tiene_resumen_ia": "generativeSummary" in data,
                    "ultima_actualizacion": data.get("utcOffsetMinutes", "N/A")
                },
                
                # Datos completos RAW (para análisis avanzado)
                "datos_completos": data
            }
            
            print(f"✓ Detalles obtenidos exitosamente para: {respuesta_estructurada['informacion_basica']['nombre']}")
            print(f"✓ Rating: {respuesta_estructurada['ratings']['rating_promedio']} ({respuesta_estructurada['ratings']['total_reviews']} reviews)")
            print(f"✓ Cache status: {respuesta_estructurada['cache_status']}")
            
            return respuesta_estructurada
            
    except Exception as e:
        print(f"ERROR: Error inesperado en obtener_detalles_lugar_v1: {e}")
        return {
            "place_id": place_id,
            "error": f"Error inesperado: {str(e)}",
            "fuente": "google_places_api_v1"
        }

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)