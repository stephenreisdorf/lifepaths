<script setup>
import CharacterCanvas from './CharacterCanvas.vue'

defineProps({
  characterData: Object,
  history: Array,
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
      :history="history"
    />
    <button class="restart-btn" @click="$emit('restart')">Start Over</button>
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
