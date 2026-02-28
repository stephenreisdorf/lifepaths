<script setup>
defineProps({
  stage: Object,
  visitCount: Number,
})
</script>

<template>
  <header class="stage-header" v-if="stage">
    <div class="stage-meta">
      <span class="stage-label">Stage</span>
      <span class="visit-badge" v-if="stage.is_repeatable && visitCount > 0">
        Visit {{ visitCount + 1 }}
      </span>
    </div>
    <h2>{{ stage.name }}</h2>
    <p>{{ stage.description }}</p>
  </header>
</template>

<style scoped>
.stage-header {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 1rem;
}

.stage-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.stage-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}

.visit-badge {
  font-size: 0.75rem;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 0.1rem 0.6rem;
  color: var(--color-text-muted);
}

h2 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

p {
  color: var(--color-text-muted);
  margin: 0;
  font-size: 0.95rem;
}
</style>
