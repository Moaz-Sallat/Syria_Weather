<template>
  <div class="map-wrapper">
    <LayerControl
      v-if="!forecastMode"
      :activeLayer="activeLayer"
      @change-layer="handleLayerChange"
    />

    <button class="fixed-points-btn" v-if="!forecastMode" @click="toggleFixedPointsMode">
      {{ fixedPointsMode ? 'رجوع للوضع الطبيعي' : 'عرض نقاط الإحداثيات' }}
    </button>

    <button class="forecast-toggle-btn" @click="toggleForecastMode">
      {{ forecastMode ? 'إغلاق التوقعات' : 'عرض توقعات الطقس' }}
    </button>

    <div id="map" ref="mapElement"></div>

    <div v-if="forecastMode" class="forecast-mini-panel">
      <div class="forecast-mini-card">
        <div class="forecast-mini-header">
          <div>
            <span class="mini-title">توقعات</span>
            <div class="mini-city">
              {{ selectedCity ? (selectedCity.name || selectedCity.name_ar || selectedCity.name_en || 'محافظة') : 'اختر محافظة' }}
            </div>
          </div>
          <button class="forecast-mini-close" type="button" @click="toggleForecastMode">×</button>
        </div>

        <div v-if="forecastItems.length" class="forecast-mini-row" role="list">
          <div v-for="day in forecastItems" :key="day.date" class="forecast-mini-item" role="listitem">
            <div class="mini-day">{{ getDayLabel(day.date) }}</div>
            <div class="mini-icon">{{ getWeatherIcon(day.weather_code) }}</div>
            <div class="mini-temps">
              <span class="mini-max">{{ day.max_temp }}°</span>
              <span class="mini-min">{{ day.min_temp }}°</span>
            </div>
          </div>
        </div>

        <div v-else class="forecast-empty mini-empty">
          {{ selectedCity ? 'لم يتم تحميل التوقعات بعد.' : 'اختر محافظة أولاً' }}
        </div>
      </div>
    </div>

    <div
      v-if="fixedPointsMode && selectedFixedPoint"
      class="point-popup"
      :style="fixedPointPopupStyle"
    >
      <h3>{{ selectedFixedPoint.name }}</h3>
      <p>خط الطول: {{ selectedFixedPoint.lon }}</p>
<p>خط العرض: {{ selectedFixedPoint.lat }}</p>

<p v-if="selectedFixedPoint.loading">جاري تحميل الطقس...</p>

<template v-else-if="selectedFixedPoint.weather">
 الحرارة: {{ selectedFixedPoint.weather.temp }}°C
  <p>سرعة الرياح: {{ selectedFixedPoint.weather.windSpeed }} م/ث</p>
</template>

<p v-else class="weather-error">تعذر تحميل بيانات الطقس</p>
   
    </div>
  </div>
</template>

<script setup>
import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import XYZ from 'ol/source/XYZ'
import { fromLonLat } from 'ol/proj'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import GeoJSON from 'ol/format/GeoJSON'
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import LayerControl from '@/components/map/LayerControl.vue'
import { apiUrl } from '@/config/api.js'

const props = defineProps({
  selectedCity: {
    type: Object,
    default: null,
  },
  cities: {
    type: Array,
    required: true,
  },
  forecast: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select-city', 'city-forecast', 'forecast-mode'])

const fixedPointsMode = ref(false)
const forecastMode = ref(false)
const selectedFixedPoint = ref(null)
const fixedPointPopupStyle = ref({})
const forecastItems = computed(() => props.forecast || [])

let selectedFixedPointCoordinate = null
let fixedPointsLayer = null
let citiesLayer = null

const fixedPoints = [
  { name: 'النقطة 1', lon: 36.30, lat: 33.51 },
  { name: 'النقطة 2', lon: 37.15, lat: 36.20 },
  { name: 'النقطة 3', lon: 39.00, lat: 35.95 },
  { name: 'النقطة 4', lon: 40.75, lat: 36.50 },
  { name: 'النقطة 5', lon: 36.75, lat: 35.12 },
  { name: 'النقطة 6', lon: 35.93, lat: 34.73 },
  { name: 'النقطة 7', lon: 36.72, lat: 34.88 },
  { name: 'النقطة 8', lon: 37.05, lat: 35.52 },
  { name: 'النقطة 9', lon: 38.30, lat: 34.55 },
  { name: 'النقطة 10', lon: 40.15, lat: 35.33 },
  { name: 'النقطة 11', lon: 36.10, lat: 32.70 },
  { name: 'النقطة 12', lon: 35.88, lat: 33.13 },
  { name: 'النقطة 13', lon: 36.45, lat: 32.52 },
  { name: 'النقطة 14', lon: 38.02, lat: 36.73 },
  { name: 'النقطة 15', lon: 41.20, lat: 37.05 },
]

let map = null
let selectedGovernorateFeature = null
let hoveredGovernorateFeature = null
let lastHoveredGovernorateName = null

const defaultGovernorateStyle = new Style({
  fill: new Fill({
    color: 'rgba(0, 0, 0, 0.01)',
  }),
  stroke: new Stroke({
    color: 'rgba(0, 0, 0, 0)',
    width: 1,
  }),
})

const hoverGovernorateStyle = new Style({
  fill: new Fill({
    color: 'rgba(30, 136, 229, 0.18)',
  }),
  stroke: new Stroke({
    color: '#1e88e5',
    width: 3,
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
  zIndex: 2,
})

function getGovernorateName(feature) {
  const props = feature.getProperties()
  return props.adm1_name1 || props.adm1_name || 'محافظة غير معروفة'
}

function normalizeArabicName(name) {
  return String(name)
    .replace(/\s/g, '')
    .replace(/[إأآا]/g, 'ا')
    .trim()
}

function findCityByGovernorateName(govName) {
  const normalizedGovName = normalizeArabicName(govName)

  return props.cities.find((city) => {
    return normalizeArabicName(city.name) === normalizedGovName
  })
}

function getDayLabel(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ar-EG', {
    weekday: 'short',
    day: 'numeric',
    month: 'numeric',
  })
}

function getWeatherIcon(code) {
  if (code == null) return '🌤️'
  if (code === 0) return '☀️'
  if (code === 1 || code === 2) return '⛅'
  if (code === 3) return '☁️'
  if (code >= 45 && code <= 48) return '🌫️'
  if (code >= 51 && code <= 57) return '🌦️'
  if (code >= 61 && code <= 65) return '🌧️'
  if (code >= 66 && code <= 67) return '🌨️'
  if (code >= 71 && code <= 77) return '❄️'
  if (code >= 80 && code <= 82) return '🌧️'
  if (code >= 95) return '⛈️'
  return '🌤️'
}

function toggleForecastMode() {
  forecastMode.value = !forecastMode.value
  if (forecastMode.value) {
    fixedPointsMode.value = false
  }
  emit('forecast-mode', forecastMode.value)
}

async function loadForecastForLocation(lat, lon) {
  try {
    const response = await fetch(
      apiUrl(`/api/weather/forecast?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`),
    )

    if (!response.ok) {
      return null
    }

    const result = await response.json()
    return result.forecast ?? null
  } catch (error) {
    console.error('Forecast fetch error:', error)
    return null
  }
}

function clearSelectedGovernorate(shouldEmit = false) {
  if (selectedGovernorateFeature) {
    selectedGovernorateFeature.setStyle(defaultGovernorateStyle)
    selectedGovernorateFeature = null
  }

  if (shouldEmit) {
    emit('select-city', null)
  }
}

async function selectGovernorate(feature) {
  clearSelectedGovernorate()

  selectedGovernorateFeature = feature
  feature.setStyle(selectedGovernorateStyle)

  const govName = getGovernorateName(feature)
  const city = findCityByGovernorateName(govName)

  if (city) {
    emit('select-city', city)
    const forecast = await loadForecastForLocation(city.lat, city.lon)
    emit('city-forecast', { city, forecast })
  } else {
    emit('select-city', {
      name: govName,
      lon: '-',
      lat: '-',
    })
  }

  map.getView().fit(feature.getGeometry().getExtent(), {
    padding: [90, 90, 90, 90],
    duration: 700,
    maxZoom: 8,
  })
}

function createFixedPointsLayer() {
  const features = fixedPoints.map((point) => {
    const feature = new Feature({
      geometry: new Point(fromLonLat([point.lon, point.lat])),
      pointData: point,
    })

    feature.setStyle(
      new Style({
        image: new Circle({
          radius: 7,
          fill: new Fill({ color: '#1e88e5' }),
          stroke: new Stroke({
            color: '#ffffff',
            width: 2,
          }),
        }),
      }),
    )

    return feature
  })

  return new VectorLayer({
    source: new VectorSource({
      features,
    }),
    zIndex: 10,
  })
}

function updateFixedPointPopupPosition() {
  if (!map || !selectedFixedPointCoordinate) return

  const pixel = map.getPixelFromCoordinate(selectedFixedPointCoordinate)

  fixedPointPopupStyle.value = {
    left: `${pixel[0]}px`,
    top: `${pixel[1]}px`,
  }
}

function toggleFixedPointsMode() {
  fixedPointsMode.value = !fixedPointsMode.value
  selectedFixedPoint.value = null
  selectedFixedPointCoordinate = null
  fixedPointPopupStyle.value = {}
  forecastMode.value = false

  if (!map) return

  if (fixedPointsMode.value) {
    if (citiesLayer) {
      citiesLayer.setVisible(false)
    }

    clearSelectedGovernorate(true)

    if (hoveredGovernorateFeature) {
      hoveredGovernorateFeature.setStyle(defaultGovernorateStyle)
      hoveredGovernorateFeature = null
    }

    lastHoveredGovernorateName = null

    if (!fixedPointsLayer) {
      fixedPointsLayer = createFixedPointsLayer()
      map.addLayer(fixedPointsLayer)
    }
  } else {
    if (citiesLayer) {
      citiesLayer.setVisible(true)
    }

    if (fixedPointsLayer) {
      map.removeLayer(fixedPointsLayer)
      fixedPointsLayer = null
    }

    map.getTargetElement().style.cursor = ''
  }
}
async function loadFixedPointWeather(point) {
  point.loading = true
  point.weather = null

  try {
    const appId = await resolveOwmAppId()

    if (!appId) {
      throw new Error('OpenWeather API key is missing')
    }

    const response = await fetch(
      `https://api.openweathermap.org/data/2.5/weather?lat=${point.lat}&lon=${point.lon}&appid=${appId}&units=metric&lang=ar`,
    )

    if (!response.ok) {
      throw new Error('Weather request failed')
    }

    const data = await response.json()

    point.weather = {
      temp: Math.round(data.main.temp),
      windSpeed: data.wind.speed,
    }
  } catch (error) {
    console.error(error)
    point.weather = null
  } finally {
    point.loading = false

    if (map) {
      map.renderSync()
    }

    updateFixedPointPopupPosition()
  }
}
onMounted(() => {
  const cityFeatures = props.cities.map((city) => {
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

  citiesLayer = new VectorLayer({
    source: new VectorSource({
      features: cityFeatures,
    }),
    zIndex: 3,
  })


  map = new Map({
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

  map.on('postrender', () => {
    updateFixedPointPopupPosition()
  })

  map.on('click', (event) => {
    if (fixedPointsMode.value) {
      let clickedPoint = null
      let clickedCoordinate = null

      map.forEachFeatureAtPixel(
        event.pixel,
        (feature, layer) => {
          if (layer === fixedPointsLayer) {
            clickedPoint = feature.get('pointData')
            clickedCoordinate = feature.getGeometry().getCoordinates()
            return true
          }

          return false
        },
        {
          hitTolerance: 8,
        },
      )

      selectedFixedPoint.value = clickedPoint
      selectedFixedPointCoordinate = clickedCoordinate

    if (clickedPoint && clickedCoordinate) {
  updateFixedPointPopupPosition()
  loadFixedPointWeather(clickedPoint)
} else {
  fixedPointPopupStyle.value = {}
}

      return
    }

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

    selectGovernorate(clickedGovernorate)
  })

  map.on('pointermove', (event) => {
    if (fixedPointsMode.value) {
      map.getTargetElement().style.cursor = 'default'
      return
    }

    if (event.dragging) return

    if (selectedGovernorateFeature) {
      map.getTargetElement().style.cursor = 'pointer'
      return
    }

    let hoveredFeature = null

    map.forEachFeatureAtPixel(
      event.pixel,
      (feature, layer) => {
        if (layer === governoratesLayer) {
          hoveredFeature = feature
          return true
        }

        return false
      },
      {
        hitTolerance: 3,
      },
    )

    if (
      hoveredGovernorateFeature &&
      hoveredGovernorateFeature !== hoveredFeature
    ) {
      hoveredGovernorateFeature.setStyle(defaultGovernorateStyle)
    }

    hoveredGovernorateFeature = hoveredFeature

    if (!hoveredFeature) {
      map.getTargetElement().style.cursor = ''
      lastHoveredGovernorateName = null
      return
    }

    map.getTargetElement().style.cursor = 'pointer'
    hoveredFeature.setStyle(hoverGovernorateStyle)

    const govName = getGovernorateName(hoveredFeature)

    if (govName === lastHoveredGovernorateName) return

    lastHoveredGovernorateName = govName

    const city = findCityByGovernorateName(govName)

    if (city) {
      emit('select-city', city)
    }
  })

  void resolveOwmAppId()
})

watch(
  () => props.selectedCity,
  (newCity) => {
    if (!newCity) {
      clearSelectedGovernorate()
    }
  },
)

function selectCityFromSearch(city) {
  if (!map) return

  const matchedFeature = governoratesSource.getFeatures().find((feature) => {
    const govName = getGovernorateName(feature)

    return normalizeArabicName(govName) === normalizeArabicName(city.name)
  })

  if (!matchedFeature) return

  selectGovernorate(matchedFeature)
}

defineExpose({
  selectCityFromSearch,
})

const activeLayer = ref('none')
let weatherLayer = null
let owmAppIdCache = ''

async function resolveOwmAppId() {
  const fromEnv = import.meta.env.VITE_OPENWEATHER_API_KEY
  if (fromEnv && String(fromEnv).trim()) {
    return String(fromEnv).trim()
  }

  if (owmAppIdCache) {
    return owmAppIdCache
  }

  try {
    const response = await fetch(apiUrl('/api/config/weather-map'))
    const data = response.ok ? await response.json() : {}
    const key = data?.apiKey != null ? String(data.apiKey).trim() : ''

    if (key) {
      owmAppIdCache = key
    }

    return key
  } catch {
    return ''
  }
}

const handleLayerChange = async (layerType) => {
  activeLayer.value = layerType

  if (!map) {
    activeLayer.value = 'none'
    return
  }

  if (weatherLayer) {
    map.removeLayer(weatherLayer)
    weatherLayer = null
  }

  if (layerType === 'none') return

  const appId = await resolveOwmAppId()

  if (!appId) {
    console.warn(
      'لا يوجد مفتاح OpenWeather: ضع OPENWEATHER_API_KEY في .env للباكند أو VITE_OPENWEATHER_API_KEY للفرونت، وتأكد أن الباكند يعمل.',
    )
    activeLayer.value = 'none'
    return
  }

  weatherLayer = new TileLayer({
    source: new XYZ({
      url: `https://tile.openweathermap.org/map/${layerType}/{z}/{x}/{y}.png?appid=${appId}`,
      crossOrigin: 'anonymous',
    }),
    zIndex: 1,
    opacity: 0.72,
  })

  map.addLayer(weatherLayer)
}

onUnmounted(() => {
  if (weatherLayer && map) {
    map.removeLayer(weatherLayer)
    weatherLayer = null
  }

  if (map) {
    map.setTarget(undefined)
    map.dispose()
    map = null
  }

  selectedGovernorateFeature = null
  hoveredGovernorateFeature = null
  lastHoveredGovernorateName = null
})
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 85vh;
}

.forecast-toggle-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 20;
  border: none;
  border-radius: 14px;
  padding: 10px 16px;
  background: #f57c00;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.forecast-toggle-btn:hover {
  background: #ef6c00;
}

/* Mini forecast panel (bottom-left) */
.forecast-mini-panel {
  position: absolute;
  bottom: 18px;
  left: 18px;
  z-index: 2200;
  width: min(92%, 380px);
  max-width: 420px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
  padding: 8px;
  backdrop-filter: blur(6px);
  border: 1px solid rgba(148, 163, 184, 0.12);
  direction: rtl;
}

.forecast-mini-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.forecast-mini-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.mini-title {
  font-weight: 800;
  color: #1d4ed8;
  font-size: 14px;
}

.mini-city {
  color: #475569;
  font-size: 12px;
}

.forecast-mini-close {
  border: none;
  background: transparent;
  font-size: 18px;
  font-weight: 800;
  cursor: pointer;
  color: #334155;
}

.forecast-mini-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 6px 2px;
}

.forecast-mini-item {
  min-width: 88px;
  flex: 0 0 auto;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid rgba(37, 99, 235, 0.08);
  padding: 8px 10px;
  text-align: right;
  color: #0f172a;
}

.mini-day { font-size: 12px; font-weight: 700; margin-bottom: 6px; }
.mini-icon { font-size: 16px; margin-bottom: 6px; }
.mini-temps { display:flex; justify-content:space-between; gap:6px; font-weight:700; color:#1e3a8a }
.mini-max { color: #dc2626 }
.mini-min { color: #2563eb }


.forecast-bottom-panel {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  width: min(90%, 760px);
  background: rgba(255, 255, 255, 0.96);
  border-radius: 20px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.18);
  padding: 14px 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.forecast-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.forecast-panel-header strong {
  color: #1d4ed8;
  font-size: 15px;
}

.forecast-city-label {
  color: #475569;
  font-size: 13px;
}

.forecast-scroll-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 6px;
}

.forecast-scroll-row::-webkit-scrollbar {
  height: 6px;
}

.forecast-scroll-row::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 999px;
}

.forecast-item {
  min-width: 100px;
  flex: 0 0 auto;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid rgba(37, 99, 235, 0.12);
  padding: 10px 12px;
  text-align: right;
  color: #0f172a;
}

.item-day {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 6px;
}

.item-icon {
  font-size: 18px;
  margin-bottom: 8px;
}

.item-temps {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-weight: 700;
  color: #1e3a8a;
}

.temp-max {
  color: #dc2626;
}

.temp-min {
  color: #2563eb;
}

.forecast-empty {
  color: #475569;
  font-size: 14px;
  text-align: center;
  padding: 8px 0;
}

.forecast-close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  border: none;
  background: transparent;
  color: #334155;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
}

.forecast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}

.forecast-grid-day {
  background: #f8fafc;
  border: 1px solid rgba(59, 130, 246, 0.14);
  border-radius: 18px;
  padding: 16px;
  text-align: right;
}

.day-label {
  margin-bottom: 10px;
  color: #1d4ed8;
  font-weight: 800;
}

.day-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.day-desc {
  color: #334155;
  margin-bottom: 12px;
}

.day-temps {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  font-weight: 700;
}

.max {
  color: #b91c1c;
}

.min {
  color: #1d4ed8;
}

.forecast-empty {
  margin: 0;
  color: #475569;
  text-align: center;
  font-weight: 600;
}

#map {
  width: 100%;
  height: 100%;
}

#map {
  width: 100%;
  height: 100%;
}

.fixed-points-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 20;
  border: none;
  border-radius: 14px;
  padding: 10px 16px;
  background: #1e88e5;
  color: white;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

.fixed-points-btn:hover {
  background: #1565c0;
}

.point-popup {
  position: absolute;
  z-index: 9999;
  min-width: 190px;
  border-radius: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
  direction: rtl;
  text-align: right;
  pointer-events: none;
  transform: translate(-50%, calc(-100% - 14px));
  backdrop-filter: blur(6px);
}

.point-popup h3 {
  margin: 0 0 10px;
  color: #1e88e5;
  font-size: 20px;
  font-weight: 800;
  text-align: center;
}

.point-popup p {
  margin: 7px 0;
  font-size: 16px;
  font-weight: 600;
  color: #222;
}
.weather-error {
  color: #e53935;
}
</style>
