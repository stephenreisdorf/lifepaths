<script setup>
import { ref } from 'vue'

defineProps({
  error: String,
  busy: Boolean,
})

defineEmits(['start'])

const anagathicsEnabled = ref(false)
</script>

<template>
  <div class="chamfer welcome-card">
    <h2>Enlistment Record</h2>
    <p>Create a character by rolling characteristics and choosing background skills, then progress through terms of service.</p>
    <label class="rule-option">
      <input v-model="anagathicsEnabled" type="checkbox" :disabled="busy">
      <span>
        <strong>Enable anagathics (anti-aging drugs)</strong>
        <small>Offers costly anti-aging treatment at the start of each career term.</small>
      </span>
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <button :disabled="busy" @click="$emit('start', anagathicsEnabled)">
      {{ busy ? 'Starting…' : 'Begin Character Creation' }}
    </button>
  </div>
</template>

<style scoped>
.welcome-card { max-width: 520px; }
.rule-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin: 1.5rem 0;
  padding: 0.85rem;
  background: var(--color-tan-shade);
  border: 1px solid var(--color-orange-dim);
  cursor: pointer;
}
.rule-option input { margin-top: 0.25rem; }
.rule-option span { display: grid; gap: 0.2rem; }
.rule-option strong { font-weight: 600; }
.rule-option small { color: var(--color-graphite-soft); line-height: 1.4; }
.rule-option:has(input:disabled) { cursor: not-allowed; opacity: 0.65; }
</style>
