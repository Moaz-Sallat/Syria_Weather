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


@app.get("/api/map/cities")
def get_cities_geojson():
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    query = """
        SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(jsonb_agg(features.feature), '[]'::jsonb)
        ) AS geojson
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'id', id,
                'geometry', ST_AsGeoJSON(geom)::jsonb,
                'properties', jsonb_build_object(
                    'id', id,
                    'name_ar', name_ar,
                    'name_en', name_en
                )
            ) AS feature
            FROM cities
        ) features;
    """

    try:
        cur.execute(query)
        result = cur.fetchone()
        return result["geojson"]
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
        # جلب آخر بيانات محفوظة خلال 30 دقيقة
        cur.execute(
            """
            SELECT temperature, humidity, description, wind_speed, last_update
            FROM weather_history
            WHERE city_id = %s
              AND last_update > NOW() - INTERVAL '30 minutes'
            ORDER BY last_update DESC
            LIMIT 1
            """,
            (city_id,),
        )

        cached = cur.fetchone()

        if cached:
            return {
                "source": "cache",
                "data": {
                    "temp": cached["temperature"],
                    "humidity": cached["humidity"],
                    "description": cached["description"],
                    "wind_speed": cached["wind_speed"],
                    "last_update": cached["last_update"],
                },
            }

        # جلب إحداثيات المدينة
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

        # طلب الطقس من OpenWeather
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

        # حفظ بيانات الطقس بالكاش
        cur.execute(
            """
            INSERT INTO weather_history
                (city_id, temperature, humidity, description, wind_speed, last_update)
            VALUES
                (%s, %s, %s, %s, %s, NOW())
            """,
            (
                city_id,
                weather_data["temp"],
                weather_data["humidity"],
                weather_data["description"],
                weather_data["wind_speed"],
            ),
        )

        conn.commit()

        return {
            "source": "live",
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