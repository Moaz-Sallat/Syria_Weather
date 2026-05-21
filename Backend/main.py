import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# تحميل ملف .env
load_dotenv()

app = FastAPI(title="Syria Weather Map API")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running"
    }
# السماح للفرونت بالاتصال مع الباك
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("OPENWEATHER_API_KEY")


def get_db_connection():
    if not DATABASE_URL:
        print("Database: DATABASE_URL is not set")
        return None
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
        conn.set_client_encoding("UTF8")
        return conn
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None


@app.get("/")
def root():
    return {"message": "Welcome to Syria Weather API"}


@app.get("/api/test-connection")
def test_connection():
    conn = get_db_connection()

    status = {
        "database": "Connected ✅" if conn else "Failed ❌",
        "api_key_loaded": "Yes ✅" if API_KEY else "No ❌",
        "database_url_found": "Yes ✅" if DATABASE_URL else "No ❌",
    }

    if conn:
        conn.close()

    return status


@app.get("/api/config/weather-map")
def weather_map_tile_key():
    """مفتاح OpenWeather لبلاط الخريطة الجوية؛ يُستخدم من الواجهة في عنوان البلاط."""
    if not API_KEY:
        return {"apiKey": None}
    return {"apiKey": API_KEY}


@app.get("/api/cities")
def list_cities():
    """قائمة المحافظات من قاعدة البيانات (للواجهة والبحث)."""
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, name_ar, name_en, lon, lat
            FROM cities
            ORDER BY id ASC
            """
        )
        rows = cur.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name_ar"],
                "name_ar": row["name_ar"],
                "name_en": row["name_en"],
                "lon": float(row["lon"]),
                "lat": float(row["lat"]),
            }
            for row in rows
        ]
    finally:
        cur.close()
        conn.close()


@app.get("/api/map/cities")
def get_cities_geojson():
    """FeatureCollection لنقاط المدن من أعمدة lon/lat (دون الحاجة لعمود geom)."""
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, name_ar, name_en, lon, lat
            FROM cities
            ORDER BY id ASC
            """
        )
        rows = cur.fetchall()
        features = []
        for row in rows:
            lon = float(row["lon"])
            lat = float(row["lat"])
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                    "properties": {
                        "id": row["id"],
                        "name_ar": row["name_ar"],
                        "name_en": row["name_en"],
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
    except Exception as e:
        print(f"Cities Query Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/weather/forecast")
def get_weather_forecast(lat: float, lon: float):
    """جلب توقع الطقس لسبعة أيام من Open-Meteo بناءً على الإحداثيات."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,windspeed_10m_max,precipitation_sum",
        "timezone": "auto",
        "forecast_days": 7,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Forecast API Error: {data.get('reason') or data.get('error') or data}",
            )

        daily = data.get("daily", {})
        forecast = []

        times = daily.get("time", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        winds = daily.get("windspeed_10m_max", [])
        precipitation = daily.get("precipitation_sum", [])
        weather_codes = daily.get("weathercode", [])

        for index, date_value in enumerate(times):
            forecast.append(
                {
                    "date": date_value,
                    "description": translate_open_meteo_code(int(weather_codes[index])) if index < len(weather_codes) else "غير متوفر",
                    "max_temp": float(highs[index]) if index < len(highs) else None,
                    "min_temp": float(lows[index]) if index < len(lows) else None,
                    "wind_speed": float(winds[index]) if index < len(winds) else None,
                    "precipitation": float(precipitation[index]) if index < len(precipitation) else None,
                    "weather_code": int(weather_codes[index]) if index < len(weather_codes) else None,
                }
            )

        return {
            "source": "open-meteo",
            "latitude": lat,
            "longitude": lon,
            "forecast": forecast,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail="تعذر جلب توقعات الطقس")


@app.get("/api/weather/{city_id}")
def get_weather(city_id: int):
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    try:
        # جلب إحداثيات المدينة فقط من جدول cities
        cur.execute(
            """
            SELECT id, name_ar, name_en, lon, lat
            FROM cities
            WHERE id = %s
            """,
            (city_id,),
        )

        city = cur.fetchone()

        if not city:
            raise HTTPException(status_code=404, detail="City not found")

        if not API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OPENWEATHER_API_KEY is missing in .env",
            )

        # جلب الطقس مباشرة من OpenWeather API بدون تخزين
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={city['lat']}"
            f"&lon={city['lon']}"
            f"&appid={API_KEY}"
            "&units=metric"
            "&lang=ar"
        )

        resp = requests.get(url, timeout=10)
        response = resp.json()

        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Weather API Error: {response.get('message')}",
            )

        weather_data = {
            "temp": response["main"]["temp"],
            "humidity": response["main"]["humidity"],
            "description": response["weather"][0]["description"],
            "wind_speed": response["wind"]["speed"],
        }

        return {
            "source": "api",
            "city": {
                "id": city["id"],
                "name_ar": city["name_ar"],
                "name_en": city["name_en"],
                "lat": city["lat"],
                "lon": city["lon"],
            },
            "data": weather_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Weather Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


WEATHER_CODE_TRANSLATIONS = {
    0: "صافي",
    1: "مشمس جزئي",
    2: "غائم جزئي",
    3: "غائم",
    45: "ضباب",
    48: "ضباب متجمد",
    51: "رذاذ خفيف",
    53: "رذاذ",
    55: "رذاذ كثيف",
    56: "رذاذ مثلج خفيف",
    57: "رذاذ مثلج كثيف",
    61: "مطر خفيف",
    63: "مطر",
    65: "مطر غزير",
    66: "مطر ثلجي خفيف",
    67: "مطر ثلجي كثيف",
    71: "ثلج خفيف",
    73: "ثلج",
    75: "ثلج غزير",
    77: "ثلوج ناعمة",
    80: "زخات مطر خفيفة",
    81: "زخات مطر",
    82: "زخات مطر غزيرة",
    85: "ثلج خفيف",
    86: "ثلج كثيف",
    95: "عاصفة رعدية",
    96: "عاصفة رعدية مع برد خفيف",
    99: "عاصفة رعدية مع برد كثيف",
}


def translate_open_meteo_code(code):
    return WEATHER_CODE_TRANSLATIONS.get(code, "حالة جوية غير معروفة")
    