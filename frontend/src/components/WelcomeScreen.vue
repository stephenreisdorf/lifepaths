<script setup>
defineEmits(['start'])
</script>

<template>
  <div class="chamfer welcome-card">
    <h2>Enlistment Record</h2>
    <p>Create a character by rolling characteristics and choosing background skills, then progress through terms of service.</p>
    <button @click="$emit('start')">Begin Character Creation</button>
  </div>
</template>

<style scoped>
.welcome-card { max-width: 520px; }
</style>
