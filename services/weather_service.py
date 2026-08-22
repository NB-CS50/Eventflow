"""Get location and weather data from Open-Meteo."""

import requests


MAJOR_CITIES = [
    {"name": "Accra", "latitude": 5.56, "longitude": -0.21},
    {"name": "Kumasi", "latitude": 6.69, "longitude": -1.62},
    {"name": "Tamale", "latitude": 9.40, "longitude": -0.84},
    {"name": "Cape Coast", "latitude": 5.11, "longitude": -1.25},
]


def geocode_location(location):
    """Find the coordinates of a location."""
    search_name = location.split(",")[0].strip()

    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": search_name, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return None
    return {
        "latitude": results[0]["latitude"],
        "longitude": results[0]["longitude"],
        "name": results[0].get("name", search_name),
        "country": results[0].get("country", ""),
    }


def get_weather(latitude, longitude):
    """Get the current weather for some coordinates."""

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,weather_code",
        },
        timeout=10,
    )
    response.raise_for_status()
    current = response.json().get("current", {})
    if current.get("temperature_2m") is None:
        raise ValueError("Weather data is missing")
    return {
        "temperature": current.get("temperature_2m"),
        "precipitation": current.get("precipitation"),
        "condition": weather_label(current.get("weather_code")),
    }


def weather_label(code):
    """Turn a weather code into a simple word."""
    match code:
        case 0:
            return "Clear"
        case 1 | 2 | 3:
            return "Cloudy"
        case 45 | 48:
            return "Foggy"
        case 51 | 53 | 55 | 61 | 63 | 65 | 80 | 81 | 82:
            return "Rainy"
        case 95 | 96 | 99:
            return "Stormy"
        case _:
            return "Unknown"


def planning_data(location):
    """Get useful planning data for an event place."""
    try:
        coordinates = geocode_location(location)
        if not coordinates:
            return {"error": "Location not found. Use a city name such as Accra, Ghana."}
        return {**coordinates, **get_weather(coordinates["latitude"], coordinates["longitude"])}
    except requests.RequestException:
        return {"error": "Weather service could not connect. Check your internet and try again."}
    except (KeyError, TypeError, ValueError):
        return {"error": "The weather service returned incomplete information."}


def major_city_weather():
    """Get current weather for major cities in Ghana."""
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": ",".join(str(city["latitude"]) for city in MAJOR_CITIES),
                "longitude": ",".join(str(city["longitude"]) for city in MAJOR_CITIES),
                "current": "temperature_2m,weather_code",
            },
            timeout=8,
        )
        response.raise_for_status()
        results = response.json()
        if not isinstance(results, list):
            results = [results]

        weather = []
        for city, result in zip(MAJOR_CITIES, results):
            current = result.get("current", {})
            weather.append(
                {
                    "name": city["name"],
                    "temperature": current.get("temperature_2m"),
                    "condition": weather_label(current.get("weather_code")),
                }
            )
        return weather
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return [{"name": city["name"], "error": "Weather unavailable"} for city in MAJOR_CITIES]
