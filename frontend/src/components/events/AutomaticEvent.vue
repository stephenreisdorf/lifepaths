<script setup>
const props = defineProps({
  event: Object,
  loading: Boolean,
})

const emit = defineEmits(['choose'])

function handleContinue() {
  if (!props.event) return
  const firstOutcome = props.event.outcomes[0]
  const choiceKeys = firstOutcome?.choice_key ? [firstOutcome.choice_key] : []
  emit('choose', { eventId: props.event.id, choiceKeys })
}
</script>

<template>
  <div class="event-panel" v-if="event">
    <h3>{{ event.name }}</h3>
    <p>{{ event.description }}</p>
    <button class="primary" @click="handleContinue" :disabled="loading">
      {{ loading ? 'Resolving...' : 'Continue' }}
    </button>
  </div>
</template>

<style scoped>
.event-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

h3 {
  font-size: 1.15rem;
  margin-bottom: 0.35rem;
}

p {
  color: var(--color-text-muted);
  margin-bottom: 1.25rem;
}
</style>
