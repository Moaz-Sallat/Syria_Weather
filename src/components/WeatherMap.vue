<template>
  <div>
    <div id="map" style="height: 500px; width: 100%;"></div>
    <button @click="toggleLayer('wind')">Toggle Wind Layer (تبديل طبقة الرياح)</button>
    <button @click="toggleLayer('temperature')">Toggle Temperature Layer (تبديل طبقة الحرارة)</button>
  </div>
</template>

<script>
import weatherMap from './weatherMap';

export default {
  mixins: [weatherMap],
};
</script>

<style>
#map {
  height: 600px;
  width: 100%;
}
</style>