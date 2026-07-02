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
      <section v-if="pendingReview" class="chamfer review-card" :data-status="reviewStatus">
        <p v-if="pendingReview.term_label" class="term-label">{{ pendingReview.term_label }}</p>
        <h2 class="review-description">{{ pendingReview.description }}</h2>
        <button @click="continueFromReview">Continue</button>
      </section>
      <div v-else-if="prompt && prompt.step_type === 'automatic'" class="chamfer prompt-card">
        <p v-if="prompt.term_label" class="term-label">{{ prompt.term_label }}</p>
        <h2>{{ prompt.description }}</h2>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="advance">Continue</button>
      </div>
      <div v-else-if="prompt" class="chamfer prompt-card">
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
.prompt-card { margin-bottom: 1rem; }
.term-label {
  font-family: var(--font-condensed);
  color: var(--color-orange);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.75rem;
  margin-bottom: 0.35rem;
}
/* Review card reuses the chamfer frame; status recolors the orange frame. */
.review-card {
  --status-accent: var(--color-orange);
  background: var(--status-accent);
  margin-bottom: 1rem;
}
.review-card[data-status="FAILED"],
.review-card[data-status="NOT_PROMOTED"],
.review-card[data-status="MISHAP"],
.review-card[data-status="AGING_CRISIS"] {
  --status-accent: var(--color-danger);
}
.review-card[data-status="PASSED"],
.review-card[data-status="QUALIFIED"],
.review-card[data-status="SURVIVED"],
.review-card[data-status="PROMOTED"] {
  --status-accent: var(--color-success);
}
.review-card .term-label { color: var(--status-accent); }
.review-description {
  margin-top: 0;
  white-space: pre-line;
  color: var(--color-graphite);
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
