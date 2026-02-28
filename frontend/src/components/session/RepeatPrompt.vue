<script setup>
defineProps({
  stage: Object,
  canRepeat: Boolean,
  loading: Boolean,
})

const emit = defineEmits(['advance'])
</script>

<template>
  <div class="repeat-panel" v-if="stage">
    <div class="repeat-badge">Stage Complete</div>
    <h3>{{ stage.name }}</h3>
    <p>{{ stage.repeat_prompt ?? 'Do you wish to repeat this stage?' }}</p>
    <div class="repeat-actions">
      <button
        v-if="canRepeat"
        class="primary"
        :disabled="loading"
        @click="emit('advance', { repeatStage: true })"
      >
        Repeat
      </button>
      <button
        class="secondary"
        :disabled="loading"
        @click="emit('advance', { repeatStage: false })"
      >
        {{ stage.default_next_stage_id ? 'Continue' : 'Finish' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.repeat-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.repeat-badge {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

h3 {
  font-size: 1.15rem;
  margin-bottom: 0.35rem;
}

p {
  color: var(--color-text-muted);
  margin-bottom: 1.25rem;
}

.repeat-actions {
  display: flex;
  gap: 0.75rem;
}
</style>
