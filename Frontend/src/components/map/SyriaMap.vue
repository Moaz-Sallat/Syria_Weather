<template>
  <div class="map-wrapper">
    <LayerControl
      :activeLayer="activeLayer"
      :owmMapAvailable="owmMapAvailable"
      @change-layer="selectLayer"
    />
    
    <div id="map" ref="mapElement"></div>
  </div>
</template>

<script setup>

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import WebGLTile from 'ol/layer/WebGLTile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import DataTile from 'ol/source/DataTile'
import VectorTile from 'ol/source/VectorTile'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import XYZ from 'ol/source/XYZ'
import MVT from 'ol/format/MVT'
import { fromLonLat } from 'ol/proj'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import GeoJSON from 'ol/format/GeoJSON'
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { addOpenLayersProtocolSupport, omProtocol } from '@openmeteo/weather-map-layer'
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
})

const emit = defineEmits(['select-city'])

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

  const citiesLayer = new VectorLayer({
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

  map.on('click', (event) => {
    let clickedGovernorate = null

    map.forEachFeatureAtPixel(
      event.pixel,
      (feature) => {
        clickedGovernorate = feature
        return true
      },
      {
        layerFilter: (layer) => layer === governoratesLayer,
        hitTolerance: 3,
      },
    )

    if (!clickedGovernorate) return

    selectGovernorate(clickedGovernorate)
  })

  map.on('pointermove', (event) => {
  if (event.dragging) return

  // إذا في محافظة محددة بالضغط أو البحث، لا تعمل hover أبداً
  if (selectedGovernorateFeature) {
    map.getTargetElement().style.cursor = 'pointer'
    return
  }

  let hoveredFeature = null

  map.forEachFeatureAtPixel(
    event.pixel,
    (feature) => {
      hoveredFeature = feature
      return true
    },
    {
      layerFilter: (layer) => layer === governoratesLayer,
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

  void resolveOwmAppId().then((key) => {
    owmMapAvailable.value = Boolean(key)
  })
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
const owmMapAvailable = ref(false)
let weatherLayer = null
let rainViewerFrame = null
let rainViewerFetchedAt = 0
let owmAppIdCache = ''

/** حرارة: Open-Meteo (DWD ICON). غيوم/هطول: OWM ثم RainViewer. رياح: OWM فقط. */
const RAINVIEWER_LAYERS = new Set(['precipitation_new', 'clouds_new'])
const OWM_ONLY_LAYERS = new Set(['wind_new'])
const WEATHER_LAYER_IDS = new Set(['temp_new', ...RAINVIEWER_LAYERS, ...OWM_ONLY_LAYERS])

const OPEN_METEO_TEMP_URL =
  'https://map-tiles.open-meteo.com/data_spatial/dwd_icon/latest.json?time_step=current_time_1H&variable=temperature_2m'

let openMeteoOlAdapter = null

const RAINVIEWER_TILE_SIZE = 512
const RAINVIEWER_MAX_ZOOM = 11

const OWM_LAYER_OPACITY = {
  precipitation_new: 0.78,
  clouds_new: 0.65,
  wind_new: 0.72,
}

function getOpenMeteoOlAdapter() {
  if (!openMeteoOlAdapter) {
    openMeteoOlAdapter = addOpenLayersProtocolSupport({
      source: { DataTile, VectorTile },
      format: { MVT },
    })
    openMeteoOlAdapter.addProtocol('om', omProtocol)
  }
  return openMeteoOlAdapter
}

function buildOpenMeteoTempSource() {
  const adapter = getOpenMeteoOlAdapter()
  return adapter.createRasterSource(`om://${OPEN_METEO_TEMP_URL}`, {
    maxZoom: 12,
  })
}

function disposeWeatherLayer() {
  if (!weatherLayer) return
  const source = weatherLayer.getSource()
  map.removeLayer(weatherLayer)
  source?.dispose?.()
  weatherLayer = null
}

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

async function getLatestRainViewerFrame() {
  const now = Date.now()
  if (rainViewerFrame && now - rainViewerFetchedAt < 5 * 60 * 1000) {
    return rainViewerFrame
  }

  try {
    const response = await fetch('https://api.rainviewer.com/public/weather-maps.json')
    if (!response.ok) return rainViewerFrame

    const data = await response.json()
    const past = data?.radar?.past
    if (!Array.isArray(past) || past.length === 0) return rainViewerFrame

    rainViewerFrame = past[past.length - 1]
    rainViewerFetchedAt = now
    return rainViewerFrame
  } catch {
    return rainViewerFrame
  }
}

function buildRainViewerTileUrl(layerId, frame) {
  if (!frame) return null

  const size = RAINVIEWER_TILE_SIZE

  if (layerId === 'precipitation_new' && frame.path) {
    const path = String(frame.path).replace(/^\//, '')
    return `https://tilecache.rainviewer.com/${path}/${size}/{z}/{x}/{y}/2/1_1.png`
  }

  if (layerId === 'clouds_new' && frame.time) {
    return `https://tilecache.rainviewer.com/v2/coverage/${frame.time}/${size}/{z}/{x}/{y}/0/0_0.png`
  }

  return null
}

function buildOwmSourceOptions(layerId, appId) {
  return {
    url: `https://tile.openweathermap.org/map/${layerId}/{z}/{x}/{y}.png?appid=${appId}`,
    crossOrigin: 'anonymous',
    maxZoom: 18,
    tileSize: 256,
    opacity: OWM_LAYER_OPACITY[layerId] ?? 0.7,
  }
}

async function buildWeatherSourceOptions(layerId) {
  const appId = await resolveOwmAppId()
  if (appId) {
    owmMapAvailable.value = true
  }

  if (OWM_ONLY_LAYERS.has(layerId)) {
    if (!appId) return null
    return buildOwmSourceOptions(layerId, appId)
  }

  if (RAINVIEWER_LAYERS.has(layerId)) {
    if (appId) {
      return buildOwmSourceOptions(layerId, appId)
    }

    const frame = await getLatestRainViewerFrame()
    const url = buildRainViewerTileUrl(layerId, frame)
    if (!url) return null

    return {
      url,
      crossOrigin: 'anonymous',
      maxZoom: RAINVIEWER_MAX_ZOOM,
      tileSize: RAINVIEWER_TILE_SIZE,
      opacity: OWM_LAYER_OPACITY[layerId] ?? 0.7,
    }
  }

  return null
}

async function selectLayer(id) {
  if (!map) {
    activeLayer.value = 'none'
    return
  }

  disposeWeatherLayer()

  if (id === 'none') {
    activeLayer.value = 'none'
    return
  }

  if (!WEATHER_LAYER_IDS.has(id)) {
    activeLayer.value = 'none'
    return
  }

  if (id === 'temp_new') {
    activeLayer.value = id
    try {
      weatherLayer = new WebGLTile({
        source: buildOpenMeteoTempSource(),
        zIndex: 1,
        opacity: 0.75,
      })
      map.getLayers().insertAt(1, weatherLayer)
    } catch (error) {
      console.warn('[Syria Weather Map] تعذّر تحميل طبقة الحرارة من Open-Meteo.', error)
      activeLayer.value = 'none'
    }
    return
  }

  const sourceOptions = await buildWeatherSourceOptions(id)
  if (!sourceOptions) {
    if (OWM_ONLY_LAYERS.has(id)) {
      console.warn(
        '[Syria Weather Map] طبقة الرياح تحتاج OPENWEATHER_API_KEY (حساب مجاني على openweathermap.org).',
      )
    } else {
      console.warn('[Syria Weather Map] تعذّر تحميل طبقة الطقس.')
    }
    activeLayer.value = 'none'
    return
  }

  activeLayer.value = id

  const { opacity, ...xyzOptions } = sourceOptions

  weatherLayer = new TileLayer({
    source: new XYZ(xyzOptions),
    zIndex: 1,
    opacity,
  })

  map.getLayers().insertAt(1, weatherLayer)
}

onUnmounted(() => {
  if (weatherLayer && map) {
    disposeWeatherLayer()
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
</style>
