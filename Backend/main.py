import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

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
        #to json
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
@app.get("/api/forecast/{city_id}")
def get_weekly_forecast(city_id: int):
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    try:
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

        url = "https://api.openweathermap.org/data/2.5/forecast"

        params = {
            "lat": city["lat"],
            "lon": city["lon"],
            "appid": API_KEY,
            "units": "metric",
            "lang": "ar",
        }

        resp = requests.get(url, params=params, timeout=10)
        response = resp.json()

        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Forecast API Error: {response.get('message', 'Unknown error')}",
            )

        daily_data = {}

        for item in response.get("list", []):
            date = item["dt_txt"].split(" ")[0]
            hour = item["dt_txt"].split(" ")[1]

            if date not in daily_data:
                daily_data[date] = []

            daily_data[date].append(item)

        forecast = []

        for date, items in list(daily_data.items())[:5]:
            selected_item = min(
                items,
                key=lambda x: abs(int(x["dt_txt"].split(" ")[1].split(":")[0]) - 12)
            )

            temps = [i["main"]["temp"] for i in items]
            weather_info = selected_item.get("weather", [{}])[0]

            rain_probability = selected_item.get("pop", 0) * 100

            forecast.append(
                {
                    "date": date,
                    "temp_day": round(selected_item["main"]["temp"]),
                    "temp_min": round(min(temps)),
                    "temp_max": round(max(temps)),
                    "humidity": selected_item["main"]["humidity"],
                    "wind_speed": selected_item["wind"]["speed"],
                    "description": weather_info.get("description", ""),
                    "icon": weather_info.get("icon", ""),
                    "rain_probability": round(rain_probability),
                }
            )

        return {
            "source": "api",
            "city": {
                "id": city["id"],
                "name_ar": city["name_ar"],
                "name_en": city["name_en"],
                "lat": city["lat"],
                "lon": city["lon"],
            },
            "data": forecast,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
    conn = get_db_connection()

    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cur = conn.cursor()

    try:
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

        url = "https://api.openweathermap.org/data/3.0/onecall"

        params = {
            "lat": city["lat"],
            "lon": city["lon"],
            "appid": API_KEY,
            "units": "metric",
            "lang": "ar",
            "exclude": "current,minutely,hourly,alerts",
        }

        resp = requests.get(url, params=params, timeout=10)
        response = resp.json()

        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Forecast API Error: {response.get('message', 'Unknown error')}",
            )

        def round_value(value):
            if isinstance(value, (int, float)):
                return round(value)
            return None

        forecast = []

        for day in response.get("daily", [])[:7]:
            weather_info = day.get("weather", [{}])[0]
            temp = day.get("temp", {})

            forecast.append(
                {
                    "date": datetime.fromtimestamp(day["dt"]).strftime("%Y-%m-%d"),
                    "temp_day": round_value(temp.get("day")),
                    "temp_min": round_value(temp.get("min")),
                    "temp_max": round_value(temp.get("max")),
                    "humidity": day.get("humidity"),
                    "wind_speed": day.get("wind_speed"),
                    "description": weather_info.get("description", ""),
                    "icon": weather_info.get("icon", ""),
                    "rain_probability": round_value(day.get("pop", 0) * 100),
                }
            )

        return {
            "source": "api",
            "city": {
                "id": city["id"],
                "name_ar": city["name_ar"],
                "name_en": city["name_en"],
                "lat": city["lat"],
                "lon": city["lon"],
            },
            "data": forecast,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()   