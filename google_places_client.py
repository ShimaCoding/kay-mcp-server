"""
Cliente para la nueva API de Google Places utilizando httpx y hishel para caché automático.
Este cliente reduce costos de API y mejora la velocidad mediante caché inteligente.
"""
import os
import json
import httpx
from hishel import CacheClient
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Cargar variables de entorno
load_dotenv()


class GooglePlacesClient:
    """
    Un cliente para la nueva API de Google Places (v1) que integra caché automático
    para reducir costos y mejorar la velocidad de respuesta.
    
    Características:
    - Usa la nueva API de Google Places v1
    - Caché automático con hishel (compatible con RFC 9111)
    - Soporte para todos los campos disponibles con comodín '*'
    - Manejo de errores robusto
    - Configuración flexible de almacenamiento de caché
    """
    
    BASE_URL = "https://places.googleapis.com/v1"
    
    def __init__(self, api_key: str, cache_storage: Optional[Any] = None):
        """
        Inicializa el cliente de Google Places.
        
        Args:
            api_key: Clave de API de Google Places
            cache_storage: Almacenamiento de caché personalizado (opcional)
                          Por defecto usa FileStorage en directorio ./cache_google_places/
        """
        if not api_key:
            raise ValueError("La clave de API de Google no puede estar vacía.")
        
        self.api_key = api_key
        
        # Configurar almacenamiento de caché
        if cache_storage is None:
            # Usar FileStorage por defecto en directorio específico
            import hishel
            cache_dir = Path("./cache_google_places")
            cache_dir.mkdir(exist_ok=True)
            cache_storage = hishel.FileStorage(base_path=cache_dir)
        
        # Inicializar cliente HTTP con caché automático
        self.client = CacheClient(
            storage=cache_storage,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
            }
        )
        
        print(f"✓ GooglePlacesClient inicializado con caché en: {cache_storage}")
    
    def get_place_details(self, place_id: str, fields: List[str] = None) -> Dict[str, Any]:
        """
        Obtiene los detalles de un lugar específico.
        La respuesta se guarda automáticamente en caché para futuras consultas.
        
        Args:
            place_id: ID único del lugar de Google Places
            fields: Lista de campos específicos a solicitar. 
                   Si no se especifica, usa ['*'] para obtener todos los campos
        
        Returns:
            Diccionario con los datos del lugar o error si falla la consulta
        """
        if fields is None:
            fields = ["*"]  # Solicitar todos los campos disponibles
        
        url = f"{self.BASE_URL}/places/{place_id}"
        headers = self.client.headers.copy()
        
        # La máscara de campos se envía como header específico
        headers["X-Goog-FieldMask"] = ",".join(fields)
        
        try:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            
            # Verificar si la respuesta vino del caché
            from_cache = response.extensions.get('from_cache', False)
            cache_status = "CACHE HIT" if from_cache else "API CALL"
            
            print(f"DEBUG: get_place_details para '{place_id}' - {cache_status}")
            
            return {
                "status": "success",
                "place_id": place_id,
                "from_cache": from_cache,
                "data": response.json()
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = f"Error HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail += f": {error_body}"
            except:
                error_detail += f": {e.response.text}"
            
            return {
                "status": "error",
                "place_id": place_id,
                "error": error_detail,
                "error_code": e.response.status_code
            }
        
        except Exception as e:
            return {
                "status": "error",
                "place_id": place_id,
                "error": f"Error inesperado: {str(e)}"
            }
    
    def search_places_text(self, query: str, location_bias: Dict[str, Any] = None, 
                          language_code: str = "es", max_results: int = 20) -> Dict[str, Any]:
        """
        Realiza búsqueda de lugares usando texto (Text Search).
        
        Args:
            query: Texto de búsqueda (ej: "restaurantes italianos en Roma")
            location_bias: Sesgo de ubicación para resultados más relevantes
            language_code: Código de idioma para resultados (default: "es")
            max_results: Número máximo de resultados (default: 20, máximo: 20)
        
        Returns:
            Diccionario con resultados de búsqueda o error
        """
        url = f"{self.BASE_URL}/places:searchText"
        
        # Configurar headers con FieldMask requerido
        headers = self.client.headers.copy()
        headers["X-Goog-FieldMask"] = "places.displayName,places.id,places.rating,places.types,places.priceLevel,places.userRatingCount,places.businessStatus,places.formattedAddress"
        
        payload = {
            "textQuery": query,
            "languageCode": language_code,
            "maxResultCount": min(max_results, 20)  # API limita a 20
        }
        
        if location_bias:
            payload["locationBias"] = location_bias
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            from_cache = response.extensions.get('from_cache', False)
            cache_status = "CACHE HIT" if from_cache else "API CALL"
            
            print(f"DEBUG: search_places_text para '{query}' - {cache_status}")
            
            result = response.json()
            
            # Guardar respuesta cruda en archivo JSON
            try:
                cache_dir = Path("./cache")
                cache_dir.mkdir(exist_ok=True)
                
                # Crear nombre de archivo único basado en query
                safe_query = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in query)[:50]
                raw_data_with_meta = {
                    "query": query,
                    "language_code": language_code,
                    "max_results": max_results,
                    "timestamp": datetime.now().isoformat(),
                    "api_source": "google_places_text_search_v1",
                    "from_cache": from_cache,
                    "total_results": len(result.get("places", [])),
                    "data": result
                }
                
                raw_file = cache_dir / f"raw_text_search_{safe_query.replace(' ', '_')}.json"
                with open(raw_file, "w", encoding="utf-8") as f:
                    json.dump(raw_data_with_meta, f, ensure_ascii=False, indent=2)
                
                print(f"✓ Búsqueda por texto guardada en: {raw_file}")
                
            except Exception as e:
                print(f"WARNING: No se pudo guardar búsqueda por texto: {e}")
            
            return {
                "status": "success",
                "query": query,
                "from_cache": from_cache,
                "total_results": len(result.get("places", [])),
                "data": result
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = f"Error HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail += f": {error_body}"
            except:
                error_detail += f": {e.response.text}"
            
            return {
                "status": "error",
                "query": query,
                "error": error_detail,
                "error_code": e.response.status_code
            }
        
        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "error": f"Error inesperado: {str(e)}"
            }
    
    def search_places_nearby(self, center: Dict[str, float], radius: float, 
                           included_types: List[str] = None, language_code: str = "es",
                           max_results: int = 20) -> Dict[str, Any]:
        """
        Realiza búsqueda de lugares cercanos (Nearby Search).
        
        Args:
            center: Centro de búsqueda {"latitude": float, "longitude": float}
            radius: Radio de búsqueda en metros (máximo: 50000)
            included_types: Tipos de lugares a incluir (opcional)
            language_code: Código de idioma (default: "es")
            max_results: Número máximo de resultados (default: 20)
        
        Returns:
            Diccionario con resultados de búsqueda o error
        """
        url = f"{self.BASE_URL}/places:searchNearby"
        
        # Configurar headers con FieldMask requerido
        headers = self.client.headers.copy()
        headers["X-Goog-FieldMask"] = "places.displayName,places.id,places.rating,places.types,places.priceLevel,places.userRatingCount,places.businessStatus,places.formattedAddress"
        
        payload = {
            "locationRestriction": {
                "circle": {
                    "center": center,
                    "radius": min(radius, 50000)  # API limita a 50km
                }
            },
            "languageCode": language_code,
            "maxResultCount": min(max_results, 20)
        }
        
        if included_types:
            payload["includedTypes"] = included_types
        
        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            from_cache = response.extensions.get('from_cache', False)
            cache_status = "CACHE HIT" if from_cache else "API CALL"
            
            print(f"DEBUG: search_places_nearby - {cache_status}")
            
            result = response.json()
            
            # Guardar respuesta cruda en archivo JSON
            try:
                cache_dir = Path("./cache")
                cache_dir.mkdir(exist_ok=True)
                
                # Crear identificador único para la búsqueda cercana
                lat_lng = f"{center['latitude']:.4f}_{center['longitude']:.4f}"
                raw_data_with_meta = {
                    "center": center,
                    "radius": radius,
                    "included_types": included_types,
                    "language_code": language_code,
                    "max_results": max_results,
                    "timestamp": datetime.now().isoformat(),
                    "api_source": "google_places_nearby_search_v1",
                    "from_cache": from_cache,
                    "total_results": len(result.get("places", [])),
                    "data": result
                }
                
                raw_file = cache_dir / f"raw_nearby_search_{lat_lng}_r{int(radius)}.json"
                with open(raw_file, "w", encoding="utf-8") as f:
                    json.dump(raw_data_with_meta, f, ensure_ascii=False, indent=2)
                
                print(f"✓ Búsqueda cercana guardada en: {raw_file}")
                
            except Exception as e:
                print(f"WARNING: No se pudo guardar búsqueda cercana: {e}")
            
            return {
                "status": "success",
                "center": center,
                "radius": radius,
                "from_cache": from_cache,
                "total_results": len(result.get("places", [])),
                "data": result
            }
            
        except httpx.HTTPStatusError as e:
            error_detail = f"Error HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail += f": {error_body}"
            except:
                error_detail += f": {e.response.text}"
            
            return {
                "status": "error",
                "center": center,
                "radius": radius,
                "error": error_detail,
                "error_code": e.response.status_code
            }
        
        except Exception as e:
            return {
                "status": "error",
                "center": center,
                "radius": radius,
                "error": f"Error inesperado: {str(e)}"
            }
    
    def close(self):
        """Cierra el cliente HTTP y limpia recursos."""
        self.client.close()
    
    def __enter__(self):
        """Soporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpieza automática al salir del context manager."""
        self.close()


def obtener_resumen_reviews_lugar(
    place_id: str,
    places_client: GooglePlacesClient
) -> Dict[str, Any]:
    """
    Obtiene específicamente el reviewSummary de un lugar.
    Este campo contiene un resumen generado por IA de las reseñas.
    
    Args:
        place_id: ID único del lugar de Google Places
        places_client: Instancia del cliente GooglePlacesClient
    
    Returns:
        Diccionario con el resumen de reseñas o información de error
    """
    # Usar solo reviewSummary para obtener resumen de reseñas generado por IA
    fields = ["reviewSummary"]
    
    result = places_client.get_place_details(place_id, fields)
    
    if result["status"] == "error":
        return result

    # Guardar respuesta cruda en archivo JSON para inspección y respaldo
    try:
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        
        # Guardar datos completos con timestamp
        raw_data_with_meta = {
            "place_id": place_id,
            "timestamp": datetime.now().isoformat(),
            "api_source": "google_places_api_v1_reviewSummary",
            "from_cache": result["from_cache"],
            "fields_requested": fields,
            "data": result["data"]
        }
        
        raw_file = cache_dir / f"raw_review_summary_{place_id}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(raw_data_with_meta, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Resumen de reseñas guardado en: {raw_file}")
        
    except Exception as e:
        print(f"WARNING: No se pudo guardar el archivo de respaldo: {e}")
    
    return result


def obtener_detalles_completos_de_lugar(
    place_id: str,
    places_client: GooglePlacesClient
) -> Dict[str, Any]:
    """
    Obtiene TODOS los detalles disponibles de un lugar usando el comodín '*'.
    Los datos se devuelven directamente desde el caché en llamadas posteriores.
    
    Args:
        place_id: ID único del lugar de Google Places
        places_client: Instancia del cliente GooglePlacesClient
    
    Returns:
        Diccionario con todos los detalles del lugar o información de error
    """
    # Usar comodín '*' para solicitar todos los campos disponibles
    fields = ["*"]
    
    result = places_client.get_place_details(place_id, fields)
    
    if result["status"] == "error":
        return result
    
    # Guardar respuesta cruda en archivo JSON para inspección y respaldo
    try:
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        
        # Guardar datos completos con timestamp
        raw_data_with_meta = {
            "place_id": place_id,
            "timestamp": datetime.now().isoformat(),
            "api_source": "google_places_api_v1",
            "from_cache": result["from_cache"],
            "data": result["data"]
        }
        
        raw_file = cache_dir / f"raw_place_details_{place_id}.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(raw_data_with_meta, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Detalles completos guardados en: {raw_file}")
        
    except Exception as e:
        print(f"WARNING: No se pudo guardar el archivo de respaldo: {e}")
    
    return result


def clasificar_lugares(places: List[Dict], query: str) -> Dict[str, List[Dict]]:
    """
    Clasifica lugares en categorías para análisis de competencia.
    
    Args:
        places: Lista de lugares obtenidos de la API
        query: Consulta original para determinar relevancia
    
    Returns:
        Diccionario con lugares clasificados por categoría
    """
    clasificados = {
        "competencia_directa": [],
        "competencia_indirecta": [],
        "colaboradores_potenciales": []
    }
    
    query_keywords = query.lower().split()
    
    for place in places:
        types = place.get("types", [])
        name = place.get("displayName", {}).get("text", "")
        name_lower = name.lower()
        
        # Lógica de clasificación mejorada
        if any(t in ["tourist_attraction", "travel_agency", "point_of_interest"] for t in types):
            # Verificar si es competencia directa por keywords
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


def buscar_lugares_con_nueva_api(query: str, ubicacion: str, radio_km: int = 50, 
                                api_key: str = None) -> Dict[str, Any]:
    """
    Función puente que usa el nuevo GooglePlacesClient para realizar búsquedas
    manteniendo compatibilidad con el formato del servidor MCP existente.
    
    Args:
        query: Tipo de negocio o actividad a buscar
        ubicacion: Ubicación donde buscar
        radio_km: Radio de búsqueda en kilómetros
        api_key: Clave de API de Google (opcional, se puede tomar de env)
    
    Returns:
        Diccionario con formato compatible con el servidor MCP existente
    """
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("WARNING: GOOGLE_API_KEY no configurada, función no disponible")
        return {"error": "API key no configurada"}
    
    try:
        with GooglePlacesClient(api_key=api_key) as client:
            # Configurar sesgo de ubicación (requiere geocodificación del ubicacion)
            # Por simplicidad, usamos búsqueda por texto con ubicación incluida
            search_query = f"{query} en {ubicacion}"
            
            print(f"🔍 Buscando '{search_query}' con nueva API v1...")
            
            # Realizar búsqueda
            result = client.search_places_text(
                query=search_query,
                language_code="es",
                max_results=20
            )
            
            if result["status"] == "error":
                return {"error": f"Error en búsqueda: {result['error']}"}
            
            # Convertir formato de nueva API al formato esperado por el servidor MCP
            places_data = result["data"].get("places", [])
            formatted_places = []
            
            for place in places_data:
                formatted_place = {
                    "place_id": place.get("id"),
                    "name": place.get("displayName", {}).get("text", "Nombre no disponible"),
                    "address": place.get("formattedAddress", "Dirección no disponible"),
                    "website": "No disponible",  # Requiere details API para obtener
                    "rating": place.get("rating", "N/A"),
                    "types": place.get("types", []),
                    "user_ratings_total": place.get("userRatingCount", 0)
                }
                formatted_places.append(formatted_place)
            
            # Clasificar lugares usando la función existente
            clasificados = clasificar_lugares(formatted_places, query)
            
            # Guardar resultado en formato JSON compatible
            try:
                cache_dir = Path("./cache")
                cache_dir.mkdir(exist_ok=True)
                
                resultado_completo = {
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
                    "fuente": "google_places_api_v1",
                    "timestamp": datetime.now().isoformat(),
                    "from_cache": result["from_cache"],
                    "raw_api_response": result["data"]  # Respuesta completa para referencia
                }
                
                # Generar nombre de archivo compatible
                import hashlib
                cache_key = hashlib.md5(f"{query.lower()}_{ubicacion.lower()}_{radio_km}".encode()).hexdigest()
                result_file = cache_dir / f"places_search_v1_{cache_key}.json"
                
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(resultado_completo, f, ensure_ascii=False, indent=2)
                
                print(f"✓ Resultado completo guardado en: {result_file}")
                
                return resultado_completo
                
            except Exception as e:
                print(f"WARNING: No se pudo guardar resultado completo: {e}")
                # Retornar resultado sin guardar
                return {
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
                    "fuente": "google_places_api_v1",
                    "from_cache": result["from_cache"]
                }
                
    except Exception as e:
        print(f"ERROR: Error en búsqueda con nueva API: {e}")
        return {"error": f"Error inesperado: {str(e)}"}


# --- Ejemplo de Uso ---
if __name__ == "__main__":
    # Cargar API Key desde variables de entorno
    API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if not API_KEY:
        print("Error: Por favor, configura la variable de entorno GOOGLE_API_KEY.")
        print("Puedes obtener una clave en: https://developers.google.com/maps/documentation/places/web-service/get-api-key")
    else:
        # Ejemplo con context manager (recomendado)
        with GooglePlacesClient(api_key=API_KEY) as g_client:
            # ID de ejemplo - Torre Eiffel
            sample_place_id = "ChIJLU7jZClu5kcR4PcOOO6p3I0"
            
            print("=== PRIMERA LLAMADA (Petición a la red, costo de API) ===")
            resultado_1 = obtener_detalles_completos_de_lugar(sample_place_id, g_client)
            
            if resultado_1['status'] == 'success':
                data = resultado_1['data']
                print(f"✓ Nombre: {data.get('displayName', {}).get('text', 'N/A')}")
                print(f"✓ Teléfono: {data.get('internationalPhoneNumber', 'No disponible')}")
                print(f"✓ Rating: {data.get('rating', 'N/A')}")
                print(f"✓ Resumen IA disponible: {'generativeSummary' in data}")
                print(f"✓ Desde caché: {resultado_1['from_cache']}")
            else:
                print("❌ Error en primera llamada:")
                print(json.dumps(resultado_1, indent=2, ensure_ascii=False))
            
            print("\n" + "="*60 + "\n")
            
            print("=== SEGUNDA LLAMADA (Lectura instantánea desde caché, sin costo) ===")
            resultado_2 = obtener_detalles_completos_de_lugar(sample_place_id, g_client)
            
            if resultado_2['status'] == 'success':
                print("✓ Datos recuperados exitosamente desde el caché.")
                print(f"✓ Desde caché: {resultado_2['from_cache']}")
                print(f"✓ Nombre: {resultado_2['data'].get('displayName', {}).get('text', 'N/A')}")
            else:
                print("❌ Error en segunda llamada:")
                print(json.dumps(resultado_2, indent=2, ensure_ascii=False))
            
            print("\n" + "="*60 + "\n")
            
            # Ejemplo de búsqueda por texto
            print("=== BÚSQUEDA POR TEXTO ===")
            search_result = g_client.search_places_text(
                query="observatorios astronómicos Valle del Elqui",
                language_code="es",
                max_results=5
            )
            
            if search_result['status'] == 'success':
                places_found = search_result['data'].get('places', [])
                print(f"✓ Encontrados {len(places_found)} lugares")
                for place in places_found[:3]:  # Mostrar solo los primeros 3
                    name = place.get('displayName', {}).get('text', 'N/A')
                    rating = place.get('rating', 'N/A')
                    print(f"  - {name} (Rating: {rating})")
            else:
                print("❌ Error en búsqueda:")
                print(json.dumps(search_result, indent=2, ensure_ascii=False))
        
        print("\n" + "="*60 + "\n")
        
        # Ejemplo usando la función puente compatible con MCP
        print("=== FUNCIÓN PUENTE COMPATIBLE CON MCP ===")
        resultado_mcp = buscar_lugares_con_nueva_api(
            query="tour astronómico",
            ubicacion="Valle del Elqui",
            radio_km=50,
            api_key=API_KEY
        )
        
        if "error" not in resultado_mcp:
            print(f"✓ Búsqueda exitosa:")
            print(f"  - Total encontrados: {resultado_mcp['total_encontrados']}")
            print(f"  - Competencia directa: {resultado_mcp['resumen']['competencia_directa']}")
            print(f"  - Competencia indirecta: {resultado_mcp['resumen']['competencia_indirecta']}")
            print(f"  - Colaboradores potenciales: {resultado_mcp['resumen']['colaboradores_potenciales']}")
            print(f"  - Desde caché: {resultado_mcp.get('from_cache', False)}")
            print(f"  - Fuente: {resultado_mcp['fuente']}")
        else:
            print("❌ Error en función puente:")
            print(json.dumps(resultado_mcp, indent=2, ensure_ascii=False))
        
        print("\n" + "="*60 + "\n")
        
        # Ejemplo usando la nueva función de reviewSummary
        print("=== RESUMEN DE RESEÑAS CON IA (reviewSummary) ===")
        sample_place_id_observatory = "ChIJ_b3MTCoakJYRv2pkmbeUgbg"  # Office Mamalluca Observatory
        
        resultado_reviews = obtener_resumen_reviews_lugar(sample_place_id_observatory, g_client)
        
        if resultado_reviews['status'] == 'success':
            review_summary = resultado_reviews['data'].get('reviewSummary')
            if review_summary:
                print(f"✓ Resumen de IA disponible:")
                print(f"  - Texto: {review_summary.get('text', 'N/A')}")
                print(f"  - Idioma: {review_summary.get('languageCode', 'N/A')}")
            else:
                print("⚠️  No hay reviewSummary disponible para este lugar")
            print(f"✓ Cache status: {'CACHE HIT' if resultado_reviews['from_cache'] else 'API CALL'}")
        else:
            print("❌ Error obteniendo resumen de reseñas:")
            print(json.dumps(resultado_reviews, indent=2, ensure_ascii=False))