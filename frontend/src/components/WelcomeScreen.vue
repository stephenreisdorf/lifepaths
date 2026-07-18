<script setup>
defineProps({
  error: String,
  busy: Boolean,
})

defineEmits(['start'])
</script>

<template>
  <div class="chamfer welcome-card">
    <h2>Enlistment Record</h2>
    <p>Create a character by rolling characteristics and choosing background skills, then progress through terms of service.</p>
    <p v-if="error" class="error">{{ error }}</p>
    <button :disabled="busy" @click="$emit('start')">
      {{ busy ? 'Starting…' : 'Begin Character Creation' }}
    </button>
  </div>
</template>

<style scoped>
.welcome-card { max-width: 520px; }
</style>
