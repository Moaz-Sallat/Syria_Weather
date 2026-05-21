<template>
  <div class="map-wrapper">
    <LayerControl
      :activeLayer="activeLayer"
      @change-layer="handleLayerChange"
    />

    <button class="fixed-points-btn" @click="toggleFixedPointsMode">
      {{ fixedPointsMode ? 'رجوع للوضع الطبيعي' : 'عرض نقاط الإحداثيات' }}
    </button>

    <div id="map" ref="mapElement"></div>

    <!-- مقياس الطبقات -->
    <div
      v-if="activeLayer !== 'none' && currentLegendConfig"
      class="weather-legend"
      dir="rtl"
    >
      <div class="legend-header">
        <span>
          {{ currentLegendConfig.icon }}
          {{ currentLegendConfig.title }}
        </span>
      </div>

      <div
        class="legend-scale"
        :style="{ background: currentLegendConfig.gradient }"
      ></div>

      <div class="legend-values">
        <span
          v-for="value in currentLegendConfig.values"
          :key="value"
        >
          {{ value }}
        </span>
      </div>

      <div class="legend-unit">
        {{ currentLegendConfig.unit }}
      </div>
    </div>

    <!-- نافذة النقاط -->
    <div
      v-if="fixedPointsMode && selectedFixedPoint"
      class="point-popup"
      :style="fixedPointPopupStyle"
    >
      <h3>{{ selectedFixedPoint.name }}</h3>

      <p>خط الطول: {{ selectedFixedPoint.lon }}</p>

      <p>خط العرض: {{ selectedFixedPoint.lat }}</p>

      <p v-if="selectedFixedPoint.loading">
        جاري تحميل الطقس...
      </p>

      <template v-else-if="selectedFixedPoint.weather">
        <p>
          الحرارة:
          {{ selectedFixedPoint.weather.temp }}°C
        </p>

        <p>
          سرعة الرياح:
          {{ selectedFixedPoint.weather.windSpeed }} م/ث
        </p>
      </template>

      <p v-else class="weather-error">
        تعذر تحميل بيانات الطقس
      </p>
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
import LayerControl from '@/components/map/LayerControl.vue'
import { apiUrl } from '@/config/api.js'
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  selectedCity: {
    type: Object,
    default: null,
  },
  cities: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['select-city'])

const fixedPointsMode = ref(false)
const selectedFixedPoint = ref(null)
const fixedPointPopupStyle = ref({})

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

function clearSelectedGovernorate(shouldEmit = false) {
  if (selectedGovernorateFeature) {
    selectedGovernorateFeature.setStyle(defaultGovernorateStyle)
    selectedGovernorateFeature = null
  }

  if (shouldEmit) {
    emit('select-city', null)
  }
}

function selectGovernorate(feature) {
  clearSelectedGovernorate()

  selectedGovernorateFeature = feature
  feature.setStyle(selectedGovernorateStyle)

  const govName = getGovernorateName(feature)
  const city = findCityByGovernorateName(govName)

  if (city) {
    emit('select-city', city)
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

const legendConfigs = {
  temp_new: {
    icon: '🌡️',
    title: 'مقياس الحرارة',
    unit: '°C',
    values: [-20, -10, 0, 10, 20, 30, 40],
    gradient:
      'linear-gradient(90deg, #6b4cc2, #3f8cff, #4fd1c5, #8bc34a, #ffe600, #ff9800, #f44336)',
  },

  precipitation_new: {
    icon: '🌧️',
    title: 'مقياس الهطول',
    unit: 'mm',
    values: [0, 1, 5, 10, 20, 50, 100],
    gradient:
      'linear-gradient(90deg, #dff6ff, #8bd3ff, #3b9cff, #0066ff, #7b2cff, #ff4fd8, #ffffff)',
  },

  wind_new: {
    icon: '💨',
    title: 'مقياس الرياح',
    unit: 'm/s',
    values: [0, 2, 5, 10, 15, 25, 35],
    gradient:
      'linear-gradient(90deg, #e0f7fa, #80deea, #26c6da, #00acc1, #00838f, #006064, #4a148c)',
  },

  clouds_new: {
    icon: '☁️',
    title: 'مقياس الغيوم',
    unit: '%',
    values: [0, 20, 40, 60, 80, 100],
    gradient:
      'linear-gradient(90deg, #ffffff, #eeeeee, #cfd8dc, #90a4ae, #607d8b, #263238)',
  },

  pressure_new: {
    icon: '🧭',
    title: 'مقياس الضغط الجوي',
    unit: 'hPa',
    values: [960, 980, 1000, 1010, 1020, 1040],
    gradient:
      'linear-gradient(90deg, #311b92, #512da8, #1976d2, #26c6da, #ffee58, #ef5350)',
  },

  snow_new: {
    icon: '❄️',
    title: 'مقياس الثلوج',
    unit: 'mm',
    values: [0, 1, 5, 10, 20, 50],
    gradient:
      'linear-gradient(90deg, #ffffff, #e0f2fe, #bae6fd, #7dd3fc, #38bdf8, #2563eb)',
  },
}

const currentLegendConfig = computed(() => {
  return legendConfigs[activeLayer.value] || null
})
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
.weather-legend {
  position: absolute;
  right: 16px;
  bottom: 16px;
  z-index: 5000;
  width: 330px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.22);
  direction: rtl;
}

.legend-header {
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: 800;
  color: #111827;
}

.legend-scale {
  height: 16px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.legend-values {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #263238;
  direction: ltr;
}

.legend-unit {
  margin-top: 6px;
  text-align: center;
  font-size: 12px;
  font-weight: 800;
  color: #607d8b;
}

@media (max-width: 720px) {
  .weather-legend {
    right: 10px;
    left: 10px;
    bottom: 10px;
    width: auto;
  }
}
</style>
