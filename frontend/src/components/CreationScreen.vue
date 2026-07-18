<script setup>
import { reactive, computed, nextTick, ref, watch } from 'vue'
import SkillGrid from './SkillGrid.vue'
import CharacterCanvas from './CharacterCanvas.vue'
import LifepathProgress from './LifepathProgress.vue'

const props = defineProps({
  characterData: Object,
  prompt: Object,
  pendingReview: Object,
  progress: Object,
  history: Array,
  error: String,
  busy: Boolean,
})

const emit = defineEmits(['confirm', 'advance', 'continue'])

const selected = reactive(new Set())
const promptHeading = ref(null)

watch(() => props.prompt, () => {
  selected.clear()
})

watch(
  [() => props.pendingReview, () => props.prompt],
  async () => {
    await nextTick()
    promptHeading.value?.focus()
  },
  { immediate: true },
)

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
const reviewStatusLabel = computed(() => {
  if (!reviewStatus.value) return 'Outcome recorded'
  return reviewStatus.value.replaceAll('_', ' ').toLowerCase()
})

const reviewStatusTone = computed(() => {
  if (['FAILED', 'NOT_PROMOTED', 'MISHAP', 'AGING_CRISIS'].includes(reviewStatus.value)) {
    return 'negative'
  }
  if (['PASSED', 'QUALIFIED', 'SURVIVED', 'PROMOTED'].includes(reviewStatus.value)) {
    return 'positive'
  }
  return 'neutral'
})
</script>

<template>
  <div class="creation-screen">
    <LifepathProgress :progress="progress" />

    <div class="creation-layout">
      <main class="prompt-column">
        <section v-if="pendingReview" class="chamfer review-card" :data-status="reviewStatus">
          <p v-if="pendingReview.term_label" class="term-label">{{ pendingReview.term_label }}</p>
          <p id="review-status" class="status-badge" :data-tone="reviewStatusTone">
            <span aria-hidden="true">{{ reviewStatusTone === 'positive' ? '✓' : reviewStatusTone === 'negative' ? '✕' : '•' }}</span>
            {{ reviewStatusLabel }}
          </p>
          <h2
            ref="promptHeading"
            class="review-description prompt-heading"
            tabindex="-1"
            aria-describedby="review-status"
          >
            {{ pendingReview.description }}
          </h2>
          <button @click="continueFromReview">Continue</button>
        </section>
        <div v-else-if="prompt && prompt.step_type === 'automatic'" class="chamfer prompt-card">
          <p v-if="prompt.term_label" class="term-label">{{ prompt.term_label }}</p>
          <h2 ref="promptHeading" class="prompt-heading" tabindex="-1">{{ prompt.description }}</h2>
          <p v-if="error" class="error">{{ error }}</p>
          <button :disabled="busy" @click="advance">
            {{ busy ? 'Working…' : 'Continue' }}
          </button>
        </div>
        <div v-else-if="prompt" class="chamfer prompt-card">
          <h2 ref="promptHeading" class="prompt-heading" tabindex="-1">{{ prompt.description }}</h2>
          <p v-if="prompt.required_count" class="skill-counter">
            Select <span>{{ prompt.required_count }}</span>:
          </p>
          <SkillGrid
            v-if="prompt.options"
            :skills="prompt.options"
            :selected="selected"
            @toggle="toggleOption"
          />
          <p v-if="prompt.required_count" class="skill-counter" role="status" aria-live="polite">
            <span>{{ selected.size }}</span> / <span>{{ prompt.required_count }}</span> selected
          </p>
          <p v-if="error" class="error">{{ error }}</p>
          <button :disabled="!canConfirm || busy" @click="confirm">
            {{ busy ? 'Working…' : 'Confirm' }}
          </button>
        </div>
      </main>

      <CharacterCanvas
        class="canvas-column"
        :age="characterData?.age"
        :characteristics="characterData?.characteristics"
        :skills="characterData?.skills"
        :cash="characterData?.cash"
        :possessions="characterData?.possessions"
        :associates="characterData?.associates"
        :history="history"
      />
    </div>
  </div>
</template>

<style scoped>
.creation-layout {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}
.creation-screen { width: 100%; }
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
.prompt-heading:focus {
  outline: 2px solid var(--color-imperial-red);
  outline-offset: 0.25rem;
}
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
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.65rem;
  padding: 0.2rem 0.55rem;
  border: 1px solid currentColor;
  color: var(--color-graphite-soft);
  font-family: var(--font-condensed);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.status-badge[data-tone="positive"] { color: var(--color-success); }
.status-badge[data-tone="negative"] { color: var(--color-danger); }
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
