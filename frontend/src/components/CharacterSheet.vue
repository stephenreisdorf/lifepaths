<script setup>
import CharacterCanvas from './CharacterCanvas.vue'

defineProps({
  characterData: Object,
  history: Array,
  error: String,
  busy: Boolean,
})

defineEmits(['restart'])
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
    <button class="restart-btn" :disabled="busy" @click="$emit('restart')">
      {{ busy ? 'Starting…' : 'Start Over' }}
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
</style>
