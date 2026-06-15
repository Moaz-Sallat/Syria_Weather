<template>
  <section class="forecast-panel">
    <button class="forecast-close" type="button" @click="$emit('close')">
      ×
    </button>

    <div class="forecast-header">
      <div>
        <h3>توقعات الطقس للأيام القادمة</h3>
        <p>{{ city.name }}</p>
      </div>
    </div>

    <div v-if="loading" class="forecast-state loading">
      جاري تحميل توقعات الطقس...
    </div>

    <div v-else-if="error" class="forecast-state error" role="alert">
      {{ error }}
    </div>

    <div v-else-if="forecast.length" class="forecast-list">
      <article
        v-for="day in forecast"
        :key="day.date"
        class="forecast-day"
      >
        <div class="day-title">
          {{ formatDay(day.date) }}
        </div>

        <div class="weather-status">
          {{ day.description || 'غير متوفر' }}
        </div>

        <div class="weather-main-temp">
          🌡️ {{ day.temp_day }}°C
        </div>

        <div class="weather-info">
          <div class="info-row">
            <span>🔥 العظمى</span>
            <strong>{{ day.temp_max }}°C</strong>
          </div>

          <div class="info-row">
            <span>❄️ الصغرى</span>
            <strong>{{ day.temp_min }}°C</strong>
          </div>

          <div class="info-row">
            <span>💧 الرطوبة</span>
            <strong>{{ day.humidity }}%</strong>
          </div>

          <div class="info-row">
            <span>🌬️ الرياح</span>
            <strong>{{ day.wind_speed }} m/s</strong>
          </div>

          <div class="info-row">
            <span>☔ الهطول</span>
            <strong>{{ day.rain_probability }}%</strong>
          </div>
        </div>
      </article>
    </div>

    <div v-else class="forecast-state muted">
      لا توجد توقعات متاحة
    </div>
  </section>
</template>

<script setup>
defineProps({
  city: {
    type: Object,
    required: true,
  },
  forecast: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: null,
  },
})

defineEmits(['close'])

function formatDay(date) {
  return new Intl.DateTimeFormat('ar-SY', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
  }).format(new Date(date))
}
</script>

<style scoped>
.forecast-panel {
  position: fixed;
  left: 24px;
  right: auto;
  bottom: 24px;
  transform: none;
  width: min(880px, calc(100% - 48px));
  max-height: 58vh;
  overflow-y: auto;
  overflow-x: hidden;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.2);
  z-index: 1300;
  direction: rtl;
  animation: forecastUpLeft 0.3s ease;
  backdrop-filter: blur(8px);
}

.forecast-close {
  position: absolute;
  top: 10px;
  left: 14px;
  border: none;
  background: transparent;
  font-size: 30px;
  color: #666;
  cursor: pointer;
}

.forecast-header {
  padding-left: 36px;
  margin-bottom: 14px;
}

.forecast-header h3 {
  margin: 0;
  color: #1565c0;
  font-size: 22px;
  font-weight: 900;
}

.forecast-header p {
  margin: 5px 0 0;
  color: #607d8b;
  font-size: 16px;
  font-weight: 800;
}

.forecast-list {
  display: grid;
  grid-template-columns: repeat(5, minmax(145px, 1fr));
  gap: 12px;
}

.forecast-day {
  background: linear-gradient(135deg, #e3f2fd, #f8fbff);
  border: 1px solid #d4eaff;
  border-radius: 18px;
  padding: 12px;
  text-align: center;
}

.day-title {
  color: #0d47a1;
  font-size: 16px;
  font-weight: 900;
  margin-bottom: 10px;
  min-height: 42px;
}

.weather-status {
  background: rgba(21, 101, 192, 0.09);
  color: #37474f;
  border-radius: 12px;
  padding: 8px;
  font-size: 14px;
  font-weight: 800;
  margin-bottom: 10px;
}

.weather-main-temp {
  color: #e65100;
  font-size: 24px;
  font-weight: 900;
  margin-bottom: 12px;
}

.weather-info {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: white;
  border-radius: 10px;
  padding: 7px 8px;
  color: #455a64;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.info-row strong {
  color: #1565c0;
  font-weight: 900;
  white-space: nowrap;
}

.forecast-state {
  padding: 24px;
  border-radius: 16px;
  text-align: center;
  font-weight: 800;
}

.forecast-state.loading {
  background: #e3f2fd;
  color: #1565c0;
}

.forecast-state.error {
  background: #ffebee;
  color: #c62828;
}

.forecast-state.muted {
  background: #eceff1;
  color: #546e7a;
}

@keyframes forecastUpLeft {
  from {
    opacity: 0;
    transform: translateY(28px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .forecast-panel {
    left: 12px;
    bottom: 12px;
    width: calc(100% - 24px);
    max-height: 65vh;
  }

  .forecast-list {
    grid-template-columns: repeat(5, 155px);
    overflow-x: auto;
    padding-bottom: 6px;
  }
}
</style>