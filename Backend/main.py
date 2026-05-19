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
    