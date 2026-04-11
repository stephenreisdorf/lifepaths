<script setup>
defineProps({
  skills: Array,
  selected: Set,
})

const emit = defineEmits(['toggle'])
</script>

<template>
  <div class="skill-grid">
    <button
      v-for="skill in skills"
      :key="skill"
      class="skill-btn"
      :class="{ selected: selected.has(skill) }"
      @click="emit('toggle', skill)"
    >
      {{ skill }}
    </button>
  </div>
</template>
