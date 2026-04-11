<script setup>
import StatsTable from './StatsTable.vue'

defineProps({
  characteristics: Object,
  skills: Array,
})

defineEmits(['restart'])
</script>

<template>
  <div>
    <h2>Character Sheet</h2>
    <h2 style="font-size: 1rem; color: #e0e0e0; margin-bottom: 0.75rem;">Characteristics</h2>
    <StatsTable :characteristics="characteristics" />
    <h2 style="font-size: 1rem; color: #e0e0e0; margin-bottom: 0.75rem;">Skills</h2>
    <div class="skill-list">
      <span v-for="skill in skills" :key="skill" class="skill-tag">{{ skill }}</span>
    </div>
    <button @click="$emit('restart')">Start Over</button>
  </div>
</template>
