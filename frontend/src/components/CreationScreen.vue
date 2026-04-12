<script setup>
import { reactive, computed, watch } from 'vue'
import SkillGrid from './SkillGrid.vue'
import CharacterCanvas from './CharacterCanvas.vue'

const props = defineProps({
  characterData: Object,
  prompt: Object,
  history: Array,
  error: String,
})

const emit = defineEmits(['confirm'])

const selected = reactive(new Set())

watch(() => props.prompt, () => {
  selected.clear()
})

function toggleOption(option) {
  if (selected.has(option)) {
    selected.delete(option)
  } else {
    selected.add(option)
  }
}

const canConfirm = computed(() => {
  if (!props.prompt?.required_count) return selected.size > 0
  return selected.size === props.prompt.required_count
})

function confirm() {
  emit('confirm', [...selected])
}
</script>

<template>
  <div class="creation-layout">
    <main class="prompt-column">
      <div v-if="prompt">
        <h2>{{ prompt.description }}</h2>
        <p v-if="prompt.required_count" class="skill-counter">
          Select <span>{{ prompt.required_count }}</span>:
        </p>
        <SkillGrid
          v-if="prompt.options"
          :skills="prompt.options"
          :selected="selected"
          @toggle="toggleOption"
        />
        <p v-if="prompt.required_count" class="skill-counter">
          <span>{{ selected.size }}</span> / <span>{{ prompt.required_count }}</span> selected
        </p>
        <p v-if="error" class="error">{{ error }}</p>
        <button :disabled="!canConfirm" @click="confirm">Confirm</button>
      </div>
    </main>

    <CharacterCanvas
      class="canvas-column"
      :characteristics="characterData?.characteristics"
      :skills="characterData?.skills"
      :history="history"
    />
  </div>
</template>

<style scoped>
.creation-layout {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}
.prompt-column {
  flex: 1 1 60%;
  min-width: 0;
}
.canvas-column {
  flex: 0 0 38%;
  position: sticky;
  top: 1rem;
}

@media (max-width: 900px) {
  .creation-layout { flex-direction: column; }
  .prompt-column,
  .canvas-column {
    flex: 1 1 auto;
    width: 100%;
    position: static;
  }
}
</style>
