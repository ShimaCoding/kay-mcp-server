# Sistema de Caché para Google Maps API

El servidor MCP ahora incluye un sistema de caché automático que guarda los resultados de las búsquedas de Google Maps para evitar requests duplicados y mejorar el rendimiento.

## Características del Sistema de Caché

### 📁 Archivos de Caché
- **`cache/geocode_cache.json`**: Almacena resultados de geocodificación (ubicación → coordenadas)
- **`cache/places_cache.json`**: Almacena resultados **procesados** de búsquedas de lugares
- **`cache/reviews_cache.json`**: Almacena análisis **procesados** de reseñas y opiniones
- **`cache/places_raw_cache.json`**: Almacena datos **RAW completos** de Google Places API
- **`cache/reviews_raw_cache.json`**: Almacena datos **RAW completos** de Google Places Details API

### ⏰ Expiración del Caché
- **Duración**: 24 horas por defecto
- **Configuración**: Modificable en `CACHE_EXPIRY_HOURS`
- **Validación**: Automática en cada consulta

### 🔑 Sistema de Claves
- **Geocode**: Clave basada en el nombre de ubicación (lowercase)
- **Places**: Hash MD5 de query + ubicación + radio_km
- **Reviews**: Clave basada en place_id directamente
- **Places RAW**: Hash MD5 de query + ubicación + radio_km (misma que places)
- **Reviews RAW**: Clave basada en place_id directamente (misma que reviews)

## Cómo Funciona

### 1. Primera Consulta
```python
# Hace request a Google Maps API
resultado = mapeo_competencia_y_colaboradores("restaurantes", "Santiago", 5)
# Guarda resultado en cache/places_cache.json
```

### 2. Consultas Posteriores
```python
# Mapeo de lugares - usa datos del caché procesado
resultado = mapeo_competencia_y_colaboradores("restaurantes", "Santiago", 5)
# ✓ Mucho más rápido

# Análisis de opiniones - usa datos del caché procesado
analisis = analizador_de_opiniones("ChIJxxxxxx")
# ✓ Instantáneo si ya fue analizado

# Acceso a datos RAW si es necesario
raw_places = get_places_raw_from_cache("restaurantes", "Santiago", 5)
raw_reviews = get_reviews_raw_from_cache("ChIJxxxxxx")
# ✓ Acceso completo a datos originales de Google API
```

## Estructura de los Archivos de Caché

### geocode_cache.json
```json
{
  "santiago": {
    "data": {
      "lat": -33.4488897,
      "lng": -70.6692655
    },
    "timestamp": "2024-08-15T10:30:00"
  }
}
```

### reviews_raw_cache.json
```json
{
  "ChIJxxxxxx": {
    "data": {
      "html_attributions": [],
      "result": {
        "name": "Observatorio Cerro Mayu",
        "rating": 4.3,
        "user_ratings_total": 150,
        "reviews": [
          {
            "author_name": "María González",
            "author_url": "https://www.google.com/maps/contrib/...",
            "language": "es",
            "profile_photo_url": "https://lh3.googleusercontent.com/...",
            "rating": 5,
            "relative_time_description": "hace 2 meses",
            "text": "Increíble experiencia astronómica...",
            "time": 1692105600
          }
        ]
      },
      "status": "OK"
    },
    "timestamp": "2024-08-15T10:30:00",
    "place_id": "ChIJxxxxxx",
    "api_source": "google_places_details_api"
  }
}
```

### places_raw_cache.json
```json
{
  "a1b2c3d4e5f6...": {
    "data": {
      "html_attributions": [],
      "results": [
        {
          "business_status": "OPERATIONAL",
          "formatted_address": "Ruta 41, Vicuña, Valle del Elqui",
          "geometry": {
            "location": {"lat": -30.1234, "lng": -70.5678},
            "viewport": {...}
          },
          "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/...",
          "icon_background_color": "#7B9EB0",
          "icon_mask_base_uri": "https://maps.gstatic.com/mapfiles/place_api/icons/...",
          "name": "Observatorio Cerro Mayu",
          "opening_hours": {"open_now": true},
          "photos": [...],
          "place_id": "ChIJxxxxxx",
          "plus_code": {...},
          "price_level": 2,
          "rating": 4.3,
          "reference": "...",
          "types": ["tourist_attraction", "point_of_interest"],
          "user_ratings_total": 150
        }
      ],
      "status": "OK"
    },
    "timestamp": "2024-08-15T10:30:00",
    "query": "tour astronómico",
    "ubicacion": "Valle del Elqui",
    "radio_km": 50,
    "api_source": "google_places_api"
  }
}
```

## Configuración

### Variables de Entorno
```bash
# API Key de Google Maps (requerida para datos reales)
set GOOGLE_API_KEY=tu_api_key_aqui
```

### Configuración del Caché
```python
# En server.py
CACHE_EXPIRY_HOURS = 24  # Cambiar duración del caché
```

## Ventajas del Sistema

### 🚀 Rendimiento
- **Primera consulta mapeo**: ~2-3 segundos (API request)
- **Primera consulta reseñas**: ~1-2 segundos (API request)
- **Consultas en caché**: ~0.1 segundos (lectura local)

### 💰 Ahorro de Costos
- Reduce requests a Google Places API y Places Details API
- Evita cargos por consultas repetidas de mapeo y análisis

### 🔄 Fallback Automático
- Si API falla → usa caché si existe
- Si caché expira → nueva consulta API
- Si todo falla → datos placeholder

## Pruebas

### Ejecutar Test del Caché
```bash
python test_completo.py
```

Este script prueba:
- ✅ Configuración de API Key
- ✅ Herramienta de mapeo con caché
- ✅ Herramienta de análisis con caché
- ✅ Sistema de archivos de caché

### Limpiar Caché Manualmente
```bash
# Eliminar archivos de caché
rmdir /s cache
```

## Logs del Sistema

El sistema muestra mensajes informativos:
```
✓ Usando geocodificación de caché para: Santiago
✓ Geocodificación guardada en caché para: Valparaíso
✓ Usando búsqueda de lugares de caché para: restaurantes en Santiago
✓ Búsqueda de lugares guardada en caché para: hoteles en Viña del Mar
✓ Usando análisis de reseñas de caché para: ChIJxxxxxx
✓ Análisis de reseñas guardado en caché para: ChIJyyyyyy
```

## Troubleshooting

### Problema: Caché No Se Crea
**Solución**: Verificar permisos de escritura en el directorio

### Problema: Datos Obsoletos
**Solución**: Eliminar archivos de caché para forzar nueva consulta

### Problema: API Key No Configurada
**Solución**: Configurar `GOOGLE_API_KEY` en variables de entorno