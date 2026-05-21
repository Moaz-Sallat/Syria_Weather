<template>
  <div class="layer-control">
    <button
      v-for="layer in layers"
      :key="layer.id"
      type="button"
      :class="{ active: activeLayer === layer.id }"
      @click="selectLayer(layer.id)"
    >
      <span v-if="layer.icon" class="icon" aria-hidden="true">{{ layer.icon }}</span>
      {{ layer.name }}
    </button>
  </div>
</template>

<script setup>
defineProps(['activeLayer'])
const emit = defineEmits(['change-layer'])

const layers = [
  { id: 'none', name: 'خريطة عادية' },
  { id: 'temp_new', name: 'حرارة', icon: '🌡️' },
  { id: 'wind_new', name: 'رياح', icon: '💨' },
  { id: 'clouds_new', name: 'غيوم', icon: '☁️' },
  { id: 'precipitation_new', name: 'هطول', icon: '🌧️' },
  { id: 'pressure_new', name: 'ضغط جوي', icon: '📉' },
  { id: 'snow_new', name: 'ثلوج', icon: '❄️' },
]

function selectLayer(id) {
  emit('change-layer', id)
}
</script>

<style scoped>
.layer-control {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  max-width: 96%;
  min-width: 320px;
  background: rgba(255, 255, 255, 0.98);
  padding: 10px 12px;
  border-radius: 999px;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(0, 0, 0, 0.09);
}

button {
  padding: 8px 10px;
  cursor: pointer;
  border: none;
  border-radius: 999px;
  background: rgba(250, 250, 250, 0.95);
  font-size: 12px;
  min-width: 92px;
  font-weight: 700;
  transition: background 0.2s, color 0.2s, transform 0.2s;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

button:hover {
  transform: translateY(-1px);
}

.icon {
  font-size: 1em;
  line-height: 1;
}

button.active {
  background: #2196f3;
  color: #fff;
}

button:hover:not(.active) {
  background: #f0f0f0;
}
</style>
