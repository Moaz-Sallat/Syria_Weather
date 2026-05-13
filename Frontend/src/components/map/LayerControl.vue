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
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  max-width: 92%;
  background: rgba(255, 255, 255, 0.92);
  padding: 8px 10px;
  border-radius: 999px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  border: 1px solid #ddd;
}

button {
  padding: 6px 12px;
  cursor: pointer;
  border: none;
  border-radius: 20px;
  background: transparent;
  font-size: 13px;
  font-weight: 700;
  transition: background 0.2s, color 0.2s;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
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
