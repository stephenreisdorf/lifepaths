<script setup>
import { ref } from 'vue'
import CharacterCanvas from './CharacterCanvas.vue'

defineProps({
  characterData: Object,
  history: Array,
  error: String,
  busy: Boolean,
})

const emit = defineEmits(['restart'])
const confirmingRestart = ref(false)

function confirmRestart() {
  emit('restart')
}
</script>

<template>
  <div class="sheet-layout">
    <h2>Character Sheet</h2>
    <CharacterCanvas
      :age="characterData?.age"
      :characteristics="characterData?.characteristics"
      :skills="characterData?.skills"
      :cash="characterData?.cash"
      :possessions="characterData?.possessions"
      :associates="characterData?.associates"
      :history="history"
    />
    <p v-if="error" class="error">{{ error }}</p>
    <div v-if="confirmingRestart" class="restart-confirmation" role="alert">
      <p>Start over and discard this completed character?</p>
      <div class="restart-actions">
        <button class="secondary-btn" :disabled="busy" @click="confirmingRestart = false">
          Keep Character
        </button>
        <button :disabled="busy" @click="confirmRestart">
          {{ busy ? 'Starting…' : 'Discard & Start Over' }}
        </button>
      </div>
    </div>
    <button v-else class="restart-btn" :disabled="busy" @click="confirmingRestart = true">
      Start Over
    </button>
  </div>
</template>

<style scoped>
.sheet-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.restart-btn {
  align-self: flex-start;
}
.restart-confirmation {
  align-self: flex-start;
  padding: 1rem;
  border: 1px solid var(--color-orange);
}
.restart-confirmation p {
  margin-bottom: 0.75rem;
  font-weight: 600;
}
.restart-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.secondary-btn {
  background: var(--color-graphite-soft);
}
.secondary-btn:hover {
  background: var(--color-graphite);
}
</style>
