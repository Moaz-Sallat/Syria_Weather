<template>
  <div class="dashboard">
    <div class="header-row">
      <h2>خريطة سوريا</h2>
      <div class="system-status">
  <span
    class="status-dot"
    :class="{
      online: systemStatus === 'online',
      offline: systemStatus === 'offline',
      checking: systemStatus === 'checking',
    }"
  ></span>

  <span class="status-text">
    {{
      systemStatus === 'online'
        ? 'النظام يعمل'
        : systemStatus === 'offline'
        ? 'النظام متوقف'
        : 'جاري التحقق...'
    }}
  </span>
</div>

      <div class="search-box">
        <input
          v-model="searchText"
          type="text"
          placeholder="ابحث عن محافظة..."
        />

        <div v-if="filteredCities.length && searchText" class="search-results">
          <button
            v-for="city in filteredCities"
            :key="city.id"
            @click="selectFromSearch(city)"
          >
            {{ city.name }}
          </button>
        </div>
      </div>
    </div>

    <SyriaMap
      ref="syriaMapRef"
      :selected-city="selectedCity"
      @select-city="handleSelectCity"
    />

    <WeatherCard
      v-if="selectedCity"
      :city="selectedCity"
      :weather="weather"
      :loading="loadingWeather"
      @close="closeCard"
    />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import SyriaMap from '@/components/map/SyriaMap.vue'
import WeatherCard from '@/components/map/WeatherCard.vue'


const selectedCity = ref(null)
const weather = ref(null)
const loadingWeather = ref(false)
const searchText = ref('')
const syriaMapRef = ref(null)
const systemStatus = ref('checking')
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

const filteredCities = computed(() => {
  const value = searchText.value.trim()

  if (!value) return []

  return cities.filter((city) => city.name.includes(value))
})
async function checkSystemHealth() {
  try {
    const response = await fetch(`${API_URL}/health`)

    if (!response.ok) {
      systemStatus.value = 'offline'
      return
    }

    const result = await response.json()

    systemStatus.value =
      result.status === 'ok'
        ? 'online'
        : 'offline'
  } catch (error) {
    systemStatus.value = 'offline'
  }
}
async function handleSelectCity(city) {
  selectedCity.value = city
  weather.value = null

  if (!city?.id) return

  loadingWeather.value = true

  try {
    const response = await fetch(`${API_URL}/api/weather/${city.id}`)
    const result = await response.json()

    weather.value = response.ok ? result.data : null
  } catch (error) {
    console.error('Weather fetch error:', error)
    weather.value = null
  } finally {
    loadingWeather.value = false
  }
}

function selectFromSearch(city) {
  searchText.value = ''
  selectedCity.value = city
  syriaMapRef.value?.selectCityFromSearch(city)
}

function closeCard() {
  selectedCity.value = null
  weather.value = null
}
onMounted(() => {
  checkSystemHealth()

  setInterval(() => {
    checkSystemHealth()
  }, 10000)
})
</script>

<style scoped>
.dashboard {
  direction: rtl;
  font-family: Arial, sans-serif;
}
.system-status {
  position: absolute;
  right: 25px;
  top: 50%;
  transform: translateY(-50%);

  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.status-dot.online {
  background: #2e7d32;
  box-shadow: 0 0 10px #2e7d32;
}

.status-dot.offline {
  background: #d32f2f;
  box-shadow: 0 0 10px #d32f2f;
}

.status-dot.checking {
  background: #f9a825;
  box-shadow: 0 0 10px #f9a825;
}

.status-text {
  font-weight: bold;
  color: #333;
}

.header-row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 12px 0;
  height: 50px;
}

h2 {
  margin: 0;
  text-align: center;
}

.search-box {
  position: absolute;
  left: 25px;
  width: 260px;
  z-index: 2000;
}

.search-box input {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid #d0d7de;
  border-radius: 12px;
  outline: none;
  font-size: 15px;
}

.search-box input:focus {
  border-color: #1e88e5;
  box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.15);
}

.search-results {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.search-results button {
  width: 100%;
  display: block;
  padding: 11px 14px;
  border: none;
  background: white;
  text-align: right;
  cursor: pointer;
  font-size: 15px;
}

.search-results button:hover {
  background: #e3f2fd;
}
</style>