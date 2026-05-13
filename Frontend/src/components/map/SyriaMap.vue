<template>
  <div class="map-wrapper">
    <LayerControl 
      :activeLayer="activeLayer" 
      @change-layer="handleLayerChange" 
    />
    
    <div id="map" ref="mapElement"></div>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import LayerControl from '@/components/map/LayerControl.vue'
import { SYRIA_GOVERNORATES as cities } from '@/data/syriaGovernorates.js'
import { apiUrl } from '@/config/api.js'

const props = defineProps({
  selectedCity: {
    type: Object,
    default: null,
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

  return cities.find((city) => {
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
  if (event.dragging) return

  // إذا في محافظة محددة بالضغط أو البحث، لا تعمل hover أبداً
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

/** يُحمّل من الباكند عند غياب VITE_OPENWEATHER_API_KEY؛ يُخزَّن فقط عند نجاح المفتاح */
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
</style>
