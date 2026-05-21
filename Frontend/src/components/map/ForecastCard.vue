<template>
  <div class="forecast-card" v-if="forecastItems.length">
    <h4>توقعات الطقس لسبعة أيام</h4>
    <p class="city-label" v-if="city">
      لمدينة: <strong>{{ city.name || city.name_ar || city.name_en || '—' }}</strong>
    </p>

    <div class="forecast-row" role="list">
      <div
        v-for="day in forecastItems"
        :key="day.date"
        class="forecast-day"
        role="listitem"
      >
        <div class="forecast-day-name">{{ getDayLabel(day.date) }}</div>
        <div class="forecast-icon">{{ getWeatherIcon(day.weather_code) }}</div>
        <div class="forecast-description">{{ day.description }}</div>
        <div class="forecast-temps">
          <span class="temp-max">{{ day.max_temp }}°</span>
          <span class="temp-min">{{ day.min_temp }}°</span>
        </div>
        <div class="forecast-meta">رياح {{ day.wind_speed }} م/ث</div>
        <div class="forecast-meta">هطول {{ day.precipitation }} مم</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  city: {
    type: Object,
    default: null,
  },
  forecast: {
    type: Array,
    default: () => [],
  },
})

const forecastItems = computed(() => props.forecast || [])

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
</script>

<style scoped>
.forecast-card {
  margin: 24px auto;
  max-width: 980px;
  padding: 0 20px 10px;
  direction: rtl;
  color: #1c1c1c;
}

.forecast-card h4 {
  margin: 0 0 12px;
  padding-left: 6px;
  font-size: 20px;
  font-weight: 800;
  color: #1565c0;
}

.forecast-row {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
}

.city-label {
  margin: 0 0 12px;
  font-size: 14px;
  color: #374151;
}

.city-label strong {
  color: #1e3a8a;
}

.forecast-row::-webkit-scrollbar {
  height: 8px;
}

.forecast-row::-webkit-scrollbar-thumb {
  background: rgba(33, 150, 243, 0.35);
  border-radius: 999px;
}

.forecast-day {
  min-width: 150px;
  flex: 0 0 auto;
  background: #ffffff;
  border: 1px solid rgba(33, 150, 243, 0.14);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 10px 24px rgba(16, 72, 147, 0.08);
  text-align: right;
  scroll-snap-align: start;
}

.forecast-day-name {
  font-size: 14px;
  font-weight: 700;
  color: #0d47a1;
  margin-bottom: 10px;
}

.forecast-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.forecast-description {
  font-size: 14px;
  margin-bottom: 12px;
  color: #334155;
}

.forecast-temps {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 16px;
}

.temp-max {
  color: #d32f2f;
  font-weight: 800;
}

.temp-min {
  color: #1976d2;
  font-weight: 700;
}

.forecast-meta {
  font-size: 13px;
  color: #556073;
  margin-bottom: 4px;
}

@media (max-width: 680px) {
  .forecast-day {
    min-width: 140px;
    padding: 14px;
  }
}
</style>
