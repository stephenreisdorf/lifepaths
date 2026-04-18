<script setup>
import { reactive, computed, watch } from 'vue'
import SkillGrid from './SkillGrid.vue'
import CharacterCanvas from './CharacterCanvas.vue'

const props = defineProps({
  characterData: Object,
  prompt: Object,
  pendingReview: Object,
  history: Array,
  error: String,
})

const emit = defineEmits(['confirm', 'advance', 'continue'])

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

function advance() {
  emit('advance')
}

function continueFromReview() {
  emit('continue')
}

const reviewStatus = computed(() => props.pendingReview?.data?.status || '')
</script>

<template>
  <div class="creation-layout">
    <main class="prompt-column">
      <section v-if="pendingReview" class="review-card" :data-status="reviewStatus">
        <p v-if="pendingReview.term_label" class="term-label">{{ pendingReview.term_label }}</p>
        <h2 class="review-description">{{ pendingReview.description }}</h2>
        <button @click="continueFromReview">Continue</button>
      </section>
      <div v-else-if="prompt && prompt.step_type === 'automatic'">
        <p v-if="prompt.term_label" class="term-label">{{ prompt.term_label }}</p>
        <h2>{{ prompt.description }}</h2>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="advance">Continue</button>
      </div>
      <div v-else-if="prompt">
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
      :age="characterData?.age"
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
.term-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.75rem;
  opacity: 0.7;
  margin-bottom: 0.25rem;
}
.review-card {
  border-left: 4px solid #6aa9ff;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  background: rgba(106, 169, 255, 0.08);
  border-radius: 4px;
}
.review-card[data-status="FAILED"],
.review-card[data-status="NOT_PROMOTED"],
.review-card[data-status="MISHAP"],
.review-card[data-status="AGING_CRISIS"] {
  border-left-color: #e06464;
  background: rgba(224, 100, 100, 0.08);
}
.review-card[data-status="PASSED"],
.review-card[data-status="QUALIFIED"],
.review-card[data-status="SURVIVED"],
.review-card[data-status="PROMOTED"] {
  border-left-color: #5fbf7b;
  background: rgba(95, 191, 123, 0.08);
}
.review-description {
  margin-top: 0;
  white-space: pre-line;
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
