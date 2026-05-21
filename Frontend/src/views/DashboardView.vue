<template>
  <div class="dashboard">
    <div class="header-row">
      <RouterLink class="back-link" to="/">الرئيسية</RouterLink>

      <h2>خريطة سوريا</h2>

      <div
        class="system-status"
        :title="
          systemStatus === 'online'
            ? 'الباكند يستجيب'
            : 'تأكد من تشغيل الخادم على المنفذ 8000'
        "
      >
        <span
          class="status-dot"
          :class="{
            online: systemStatus === 'online',
            offline: systemStatus === 'offline',
            checking: systemStatus === 'checking',
          }"
        />
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
          type="search"
          autocomplete="off"
          placeholder="ابحث عن محافظة..."
          aria-label="بحث عن محافظة"
          :disabled="citiesLoading || !!citiesLoadError || !cities.length"
        />

        <div v-if="filteredCities.length && searchText" class="search-results" role="listbox">
          <button
            v-for="city in filteredCities"
            :key="city.id"
            type="button"
            role="option"
            @click="selectFromSearch(city)"
          >
            {{ city.name }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="citiesLoading" class="map-state loading">جاري تحميل المحافظات من الخادم...</div>
    <div v-else-if="citiesLoadError" class="map-state error" role="alert">
      {{ citiesLoadError }}
    </div>
    <div v-else-if="!cities.length" class="map-state error">
      لا توجد محافظات في قاعدة البيانات.
    </div>

    <SyriaMap
      v-else
      ref="syriaMapRef"
      :cities="cities"
      :selected-city="selectedCity"
      :forecast="forecast"
      @select-city="handleSelectCity"
      @city-forecast="handleCityForecast"
      @forecast-mode="handleMapForecastMode"
    />

    <WeatherCard
      v-if="selectedCity"
      :city="selectedCity"
      :weather="weather"
      :loading="loadingWeather"
      :error="weatherError"
      @close="closeCard"
    />

    <ForecastCard
      v-if="forecast && forecast.length && !mapForecastOpen"
      :city="selectedCity"
      :forecast="forecast"
    />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import SyriaMap from '@/components/map/SyriaMap.vue'
import WeatherCard from '@/components/map/WeatherCard.vue'
import ForecastCard from '@/components/map/ForecastCard.vue'
import { apiUrl } from '@/config/api.js'
import { fetchCities } from '@/api/cities.js'

const cities = ref([])
const citiesLoading = ref(true)
const citiesLoadError = ref(null)

const selectedCity = ref(null)
const weather = ref(null)
const weatherError = ref(null)
const forecast = ref(null)
const forecastError = ref(null)
const loadingWeather = ref(false)
const loadingForecast = ref(false)
const mapForecastOpen = ref(false)
const searchText = ref('')
const syriaMapRef = ref(null)
const systemStatus = ref('checking')

let healthPollId = null

const filteredCities = computed(() => {
  const value = searchText.value.trim()
  if (!value) return []
  return cities.value.filter((city) => city.name.includes(value))
})

function parseWeatherError(data) {
  const detail = data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || String(item)).join('، ')
  }
  if (typeof detail === 'string') return detail
  return 'تعذر جلب الطقس'
}

async function checkSystemHealth() {
  try {
    const response = await fetch(apiUrl('/health'))
    if (!response.ok) {
      systemStatus.value = 'offline'
      return
    }
    const result = await response.json()
    systemStatus.value = result.status === 'ok' ? 'online' : 'offline'
  } catch {
    systemStatus.value = 'offline'
  }
}

async function loadCities() {
  citiesLoading.value = true
  citiesLoadError.value = null
  try {
    cities.value = await fetchCities()
  } catch (e) {
    cities.value = []
    citiesLoadError.value =
      e instanceof Error ? e.message : 'فشل تحميل قائمة المحافظات'
  } finally {
    citiesLoading.value = false
  }
}

async function handleSelectCity(payload) {
  const city = payload?.city || payload
  selectedCity.value = city
  weather.value = null
  weatherError.value = null
  forecast.value = payload?.forecast ?? null
  forecastError.value = null

  if (!city?.id) {
    loadingWeather.value = false
    loadingForecast.value = false
    return
  }

  loadingWeather.value = true
  loadingForecast.value = !Boolean(forecast.value)

  try {
    const response = await fetch(apiUrl(`/api/weather/${city.id}`))
    const result = await response.json()

    if (!response.ok) {
      weather.value = null
      weatherError.value = parseWeatherError(result)
    } else {
      weather.value = result.data ?? null
      if (!weather.value) {
        weatherError.value = 'لا توجد بيانات طقس'
      }
    }
  } catch (error) {
    console.error('Weather fetch error:', error)
    weather.value = null
    weatherError.value = 'خطأ في الاتصال بالخادم'
  } finally {
    loadingWeather.value = false
  }

  if (!forecast.value && city?.lat != null && city?.lon != null) {
    await loadForecast(city.lat, city.lon)
  }
}

async function handleCityForecast(payload) {
  forecast.value = payload?.forecast ?? null
  forecastError.value = null
}

function handleMapForecastMode(isOpen) {
  mapForecastOpen.value = Boolean(isOpen)
}

async function loadForecast(lat, lon) {
  loadingForecast.value = true
  forecastError.value = null

  try {
    const response = await fetch(
      apiUrl(`/api/weather/forecast?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`),
    )
    const result = await response.json()

    if (!response.ok) {
      forecast.value = null
      forecastError.value = parseWeatherError(result)
      return
    }

    forecast.value = result.forecast ?? null
    if (!forecast.value || !forecast.value.length) {
      forecastError.value = 'تعذر الحصول على توقعات الطقس'
    }
  } catch (error) {
    console.error('Forecast fetch error:', error)
    forecast.value = null
    forecastError.value = 'خطأ في الاتصال بخادم التوقعات'
  } finally {
    loadingForecast.value = false
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
  weatherError.value = null
}

onMounted(() => {
  checkSystemHealth()
  healthPollId = window.setInterval(checkSystemHealth, 10000)
  loadCities()
})

onUnmounted(() => {
  if (healthPollId != null) {
    clearInterval(healthPollId)
    healthPollId = null
  }
})
</script>

<style scoped>
.dashboard {
  direction: rtl;
  font-family: 'Cairo', sans-serif;
  background: #f4f7fb;
  min-height: 100vh;
}

.map-state {
  margin: 24px auto;
  max-width: 560px;
  padding: 24px 28px;
  border-radius: 16px;
  text-align: center;
  font-weight: 700;
  font-size: 16px;
}

.map-state.loading {
  background: #e3f2fd;
  color: #1565c0;
}

.map-state.error {
  background: #ffebee;
  color: #c62828;
}

.header-row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 30px;
  margin-bottom: 10px;
  background: white;
  border-radius: 0 0 22px 22px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
}

.back-link {
  position: absolute;
  left: 24px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  font-weight: 700;
  color: #1565c0;
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 12px;
  transition: background 0.2s;
}

.back-link:hover {
  background: #e3f2fd;
}

.back-link:focus-visible {
  outline: 2px solid #1565c0;
  outline-offset: 2px;
}

h2 {
  margin: 0;
  font-size: clamp(28px, 5vw, 42px);
  font-weight: 800;
  color: #1565c0;
  letter-spacing: 1px;
}

.search-box {
  position: absolute;
  left: 25px;
  width: min(280px, 42vw);
  z-index: 2000;
}

.search-box input {
  width: 100%;
  padding: 14px 18px;
  border: 1px solid #dce3ea;
  border-radius: 16px;
  outline: none;
  font-size: 15px;
  background: #f8fbff;
  transition: 0.25s;
}

.search-box input:focus {
  border-color: #1e88e5;
  background: white;
  box-shadow: 0 0 0 4px rgba(30, 136, 229, 0.12);
}

.search-box input:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.search-results {
  position: absolute;
  top: 58px;
  left: 0;
  right: 0;
  max-height: 280px;
  overflow-y: auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14);
}

.search-results button {
  width: 100%;
  display: block;
  padding: 14px 18px;
  border: none;
  background: white;
  text-align: right;
  cursor: pointer;
  font-size: 15px;
  transition: 0.2s;
}

.search-results button:hover {
  background: #e3f2fd;
  color: #1565c0;
}

.system-status {
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fbff;
  padding: 10px 16px;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}

.status-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.online {
  background: #2e7d32;
  box-shadow: 0 0 14px #2e7d32;
}

.status-dot.offline {
  background: #d32f2f;
  box-shadow: 0 0 14px #d32f2f;
}

.status-dot.checking {
  background: #f9a825;
  box-shadow: 0 0 14px #f9a825;
}

.status-text {
  font-weight: 700;
  color: #333;
  font-size: 14px;
}

@media (max-width: 900px) {
  .back-link {
    position: static;
    transform: none;
    margin-bottom: 8px;
  }

  .header-row {
    flex-direction: column;
    padding-top: 48px;
    padding-bottom: 20px;
  }

  .system-status {
    position: static;
    transform: none;
    margin-top: 8px;
  }

  .search-box {
    position: static;
    width: 100%;
    max-width: 360px;
    margin-top: 16px;
  }
}
</style>
