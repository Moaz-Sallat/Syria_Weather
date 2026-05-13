<template>
  <div class="weather-card">
    <button class="close-btn" @click="$emit('close')">×</button>

    <h3>{{ city.name }}</h3>
    <p class="subtitle">معلومات المحافظة المختارة</p>

    <div class="info-row">
      <span>خط الطول</span>
      <strong>{{ city.lon }}</strong>
    </div>

    <div class="info-row">
      <span>خط العرض</span>
      <strong>{{ city.lat }}</strong>
    </div>

    <div v-if="loading" class="weather-placeholder loading">
      جاري تحميل الطقس...
    </div>

    <div v-else-if="error" class="weather-placeholder error" role="alert">
      {{ error }}
    </div>

    <div v-else-if="weather" class="weather-placeholder">
      🌡️ الحرارة: {{ weather.temp }}°C<br />
      💧 الرطوبة: {{ weather.humidity }}%<br />
      🌬️ سرعة الرياح: {{ weather.wind_speed }} m/s<br />
      ☁️ الحالة: {{ weather.description }}
    </div>

    <div v-else class="weather-placeholder muted">
      لا توجد بيانات طقس
    </div>
  </div>
</template>

<script setup>
defineProps({
  city: {
    type: Object,
    required: true,
  },
  weather: {
    type: Object,
    default: null,
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
</script>

<style scoped>
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

.weather-placeholder.error {
  background: #ffebee;
  color: #c62828;
}

.weather-placeholder.muted {
  color: #546e7a;
  background: #eceff1;
}

.weather-placeholder.loading {
  color: #1565c0;
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