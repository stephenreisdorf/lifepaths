<script setup>
defineProps({
  stageHistory: Array,
})
</script>

<template>
  <div class="history-list">
    <div
      v-for="stage in stageHistory"
      :key="`${stage.stage_id}-${stage.visit_number}`"
      class="history-item"
    >
      <div class="history-meta">
        <span class="history-stage">{{ stage.stage_name }}</span>
        <span class="history-visit" v-if="stage.visit_number > 1">
          Visit {{ stage.visit_number }}
        </span>
      </div>
      <ul class="narrative-list" v-if="stage.narrative_fragments.length > 0">
        <li v-for="(fragment, i) in stage.narrative_fragments" :key="i">{{ fragment }}</li>
      </ul>
      <div class="stage-effects" v-if="stage.features_gained.length > 0">
        <span class="gained-label">Gained:</span>
        {{ stage.features_gained.join(', ') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.history-item {
  border-left: 3px solid var(--color-accent);
  padding-left: 1rem;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}

.history-stage {
  font-weight: 600;
}

.history-visit {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  background: var(--color-surface-raised);
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
}

.narrative-list {
  margin: 0 0 0.4rem;
  padding: 0 0 0 1rem;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.narrative-list li {
  margin-bottom: 0.2rem;
}

.stage-effects {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.gained-label {
  font-weight: 500;
  color: var(--color-text);
}
</style>
