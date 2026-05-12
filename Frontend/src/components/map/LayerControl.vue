<template>
  <div class="layer-control">
    <button 
      v-for="layer in layers" 
      :key="layer.id"
      :class="{ active: activeLayer === layer.id }"
      @click="selectLayer(layer.id)"
    >
      <i v-if="layer.id === 'temp_new'" class="icon">🌡️</i>
      <i v-if="layer.id === 'wind_new'" class="icon">💨</i>
      {{ layer.name }}
    </button>
  </div>
</template>

<style scoped>
.layer-control {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px;
  border-radius: 50px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: row;
  gap: 10px;
  border: 1px solid #ddd;
}

button {
  padding: 8px 16px;
  cursor: pointer;
  border: none;
  border-radius: 25px;
  background: transparent;
  transition: all 0.3s;
  font-weight: bold;
  white-space: nowrap;
}

button.active {
  background: #2196F3;
  color: white;
}

button:hover:not(.active) {
  background: #f0f0f0;
}
</style>

<script setup>
import { ref } from 'vue';

const props = defineProps(['activeLayer']);
const emit = defineEmits(['change-layer']);

const layers = [
  { id: 'none', name: 'خريطة عادية' },
  { id: 'temp_new', name: 'حرارة' },
  { id: 'wind_new', name: 'رياح' },
  { id: 'clouds_new', name: 'غيوم' }
];

const selectLayer = (id) => {
  emit('change-layer', id);
};
</script>

<style scoped>
.layer-control {
  position: absolute;
  bottom: 30px; 
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  display: flex;
  flex-direction: row;
  gap: 5px;
  background: rgba(255, 255, 255, 0.9);
  padding: 5px;
  border-radius: 50px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border: 1px solid #ddd;
  width: auto; 
  max-width: 90%;
}

button {
  padding: 6px 12px;
  cursor: pointer;
  border: none;
  border-radius: 20px;
  background: transparent;
  font-size: 13px; 
  font-weight: bold;
  transition: all 0.3s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

button.active {
  background: #2196F3;
  color: white;
}

button:hover:not(.active) {
  background: #f0f0f0;
}
</style>