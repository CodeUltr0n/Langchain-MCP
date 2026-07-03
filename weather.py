from mcp.server.fastmcp import FastMCP
import httpx
from urllib.parse import quote

mcp = FastMCP("Weather")

def get_weather_desc(code: int) -> str:
    codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return codes.get(code, "Unknown weather condition")

@mcp.tool()
async def get_wether(location: str) -> str:
    """Get the weather for a given location (e.g. city name)"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(location)}&count=1&language=en&format=json"
            geo_resp = await client.get(geo_url)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            
            if not geo_data.get("results"):
                return f"Error: Could not find location '{location}'."
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            resolved_name = f"{result.get('name')}, {result.get('admin1', '')} ({result.get('country_code', '').upper()})"
            
            # Step 2: Forecast
            forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
            weather_resp = await client.get(forecast_url)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()
            
            current = weather_data.get("current", {})
            temp = current.get("temperature_2m")
            feels_like = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            precipitation = current.get("precipitation")
            wind_speed = current.get("wind_speed_10m")
            w_code = current.get("weather_code", 0)
            condition = get_weather_desc(w_code)
            
            units = weather_data.get("current_units", {})
            temp_unit = units.get("temperature_2m", "°C")
            wind_unit = units.get("wind_speed_10m", "km/h")
            precip_unit = units.get("precipitation", "mm")
            
            return (
                f"Current weather for {resolved_name}:\n"
                f"- Temperature: {temp}{temp_unit} (Feels like: {feels_like}{temp_unit})\n"
                f"- Condition: {condition}\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind_speed} {wind_unit}\n"
                f"- Precipitation: {precipitation} {precip_unit}"
            )
            
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")