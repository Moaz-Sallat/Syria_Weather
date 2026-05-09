<template>
  <div class="dashboard">
    <h2>خريطة سوريا</h2>

    <div id="map"></div>

    <div v-if="selectedCity" class="weather-card">
      <button class="close-btn" @click="closeCard">×</button>

      <h3>{{ selectedCity.name }}</h3>
      <p class="subtitle">معلومات المحافظة المختارة</p>

      <div class="info-row">
        <span>خط الطول</span>
        <strong>{{ selectedCity.lon }}</strong>
      </div>

      <div class="info-row">
        <span>خط العرض</span>
        <strong>{{ selectedCity.lat }}</strong>
      </div>

      <div class="weather-placeholder" v-if="loadingWeather">
        جاري تحميل الطقس...
      </div>

      <div class="weather-placeholder" v-else-if="weather">
        🌡️ الحرارة: {{ weather.temp }}°C<br />
        💧 الرطوبة: {{ weather.humidity }}%<br />
        🌬️ سرعة الرياح: {{ weather.wind_speed }} m/s<br />
        ☁️ الحالة: {{ weather.description }}
      </div>

      <div class="weather-placeholder" v-else>
        لا توجد بيانات طقس
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { fromLonLat } from 'ol/proj'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import GeoJSON from 'ol/format/GeoJSON'

const selectedCity = ref(null)
const weather = ref(null)
const loadingWeather = ref(false)

const API_URL = 'http://127.0.0.1:8000'

const cities = [
  { id: 1, name: 'دمشق', lon: 36.2765, lat: 33.5138 },
  { id: 2, name: 'ريف دمشق', lon: 36.4316, lat: 33.5167 },
  { id: 3, name: 'حلب', lon: 37.1612, lat: 36.2021 },
  { id: 4, name: 'حمص', lon: 36.7234, lat: 34.7324 },
  { id: 5, name: 'حماة', lon: 36.7578, lat: 35.1318 },
  { id: 6, name: 'اللاذقية', lon: 35.7796, lat: 35.5317 },
  { id: 7, name: 'طرطوس', lon: 35.8866, lat: 34.8959 },
  { id: 8, name: 'إدلب', lon: 36.6339, lat: 35.9306 },
  { id: 9, name: 'درعا', lon: 36.1021, lat: 32.6189 },
  { id: 10, name: 'السويداء', lon: 36.5695, lat: 32.709 },
  { id: 11, name: 'القنيطرة', lon: 35.8246, lat: 33.1259 },
  { id: 12, name: 'دير الزور', lon: 40.1408, lat: 35.3359 },
  { id: 13, name: 'الحسكة', lon: 40.7477, lat: 36.5079 },
  { id: 14, name: 'الرقة', lon: 39.0193, lat: 35.9528 },
]

let selectedGovernorateFeature = null

const defaultGovernorateStyle = new Style({
  fill: new Fill({
    color: 'rgba(0, 0, 0, 0.01)',
  }),
  stroke: new Stroke({
    color: 'rgba(0, 0, 0, 0)',
    width: 1,
  }),
})

const selectedGovernorateStyle = new Style({
  fill: new Fill({
    color: 'rgba(229, 57, 53, 0.25)',
  }),
  stroke: new Stroke({
    color: '#e53935',
    width: 4,
  }),
})

const governoratesSource = new VectorSource({
  url: '/data/syr_admin_boundaries.geojson/syr_admin1.geojson',
  format: new GeoJSON({
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857',
  }),
})

const governoratesLayer = new VectorLayer({
  source: governoratesSource,
  style: defaultGovernorateStyle,
})

function closeCard() {
  selectedCity.value = null
  weather.value = null

  if (selectedGovernorateFeature) {
    selectedGovernorateFeature.setStyle(defaultGovernorateStyle)
    selectedGovernorateFeature = null
  }
}

async function fetchWeather(city) {
  weather.value = null
  loadingWeather.value = true

  try {
    const response = await fetch(`${API_URL}/api/weather/${city.id}`)
    const result = await response.json()

    if (!response.ok) {
      weather.value = null
      return
    }

    weather.value = result.data
  } catch (error) {
    console.error('Weather fetch error:', error)
    weather.value = null
  } finally {
    loadingWeather.value = false
  }
}

function getGovernorateName(feature) {
  const props = feature.getProperties()

  return props.adm1_name1 || props.adm1_name || 'محافظة غير معروفة'
}

function findCityByGovernorateName(govName) {
  const normalizedName = String(govName).trim()

  return cities.find(
    (city) =>
      city.name.trim() === normalizedName ||
      normalizedName.includes(city.name) ||
      city.name.includes(normalizedName),
  )
}

onMounted(() => {
  const cityFeatures = cities.map((city) => {
    const feature = new Feature({
      geometry: new Point(fromLonLat([city.lon, city.lat])),
      cityData: city,
    })

    feature.setStyle(
      new Style({
        image: new Circle({
          radius: 8,
          fill: new Fill({ color: '#e53935' }),
          stroke: new Stroke({
            color: '#ffffff',
            width: 3,
          }),
        }),
      }),
    )

    return feature
  })

  const citiesLayer = new VectorLayer({
    source: new VectorSource({
      features: cityFeatures,
    }),
  })

  const map = new Map({
    target: 'map',
    layers: [
      new TileLayer({
        source: new OSM(),
      }),
      governoratesLayer,
      citiesLayer,
    ],
    view: new View({
      center: fromLonLat([38, 35]),
      zoom: 6,
      minZoom: 6,
      maxZoom: 11,
    }),
  })

  map.on('click', (event) => {
    let clickedGovernorate = null

    map.forEachFeatureAtPixel(
      event.pixel,
      (feature, layer) => {
        if (layer === governoratesLayer) {
          clickedGovernorate = feature
          return true
        }

        return false
      },
      {
        hitTolerance: 3,
      },
    )

    if (!clickedGovernorate) return

    if (selectedGovernorateFeature) {
      selectedGovernorateFeature.setStyle(defaultGovernorateStyle)
    }

    selectedGovernorateFeature = clickedGovernorate
    clickedGovernorate.setStyle(selectedGovernorateStyle)

    const govName = getGovernorateName(clickedGovernorate)
    const city = findCityByGovernorateName(govName)

    if (city) {
      selectedCity.value = city
      fetchWeather(city)
    } else {
      selectedCity.value = {
        name: govName,
        lon: '-',
        lat: '-',
      }
      weather.value = null
    }

    map.getView().fit(clickedGovernorate.getGeometry().getExtent(), {
      padding: [90, 90, 90, 90],
      duration: 700,
      maxZoom: 8,
    })
  })
})
</script>

<style scoped>
.dashboard {
  direction: rtl;
  font-family: Arial, sans-serif;
}

h2 {
  text-align: center;
  margin: 12px 0;
}

#map {
  width: 100%;
  height: 85vh;
}

.weather-card {
  position: fixed;
  top: 90px;
  right: 25px;
  width: 280px;
  background: white;
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  z-index: 1000;
  animation: slideIn 0.35s ease;
}

.close-btn {
  position: absolute;
  top: 10px;
  left: 12px;
  border: none;
  background: transparent;
  font-size: 28px;
  cursor: pointer;
  color: #777;
}

.weather-card h3 {
  margin: 5px 0;
  font-size: 26px;
  color: #1e88e5;
}

.subtitle {
  color: #777;
  margin-bottom: 18px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 10px;
  margin-bottom: 10px;
}

.weather-placeholder {
  margin-top: 15px;
  padding: 14px;
  background: linear-gradient(135deg, #e3f2fd, #e0f7fa);
  border-radius: 12px;
  text-align: center;
  font-weight: bold;
  color: #0277bd;
  line-height: 1.9;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(40px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>