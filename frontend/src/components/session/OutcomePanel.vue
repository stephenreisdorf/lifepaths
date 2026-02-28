<script setup>
defineProps({
  outcome: Object,
  sessionComplete: Boolean,
})

const emit = defineEmits(['dismissed'])
</script>

<template>
  <div class="outcome-overlay" v-if="outcome">
    <div class="outcome-card">
      <div class="outcome-badge">Outcome</div>
      <h2>{{ outcome.label }}</h2>
      <p>{{ outcome.description }}</p>

      <div
        class="effects"
        v-if="outcome.attribute_modifiers?.length > 0 || outcome.features_granted?.length > 0"
      >
        <div class="modifiers" v-if="outcome.attribute_modifiers?.length > 0">
          <div class="effects-label">Attribute Changes</div>
          <div
            v-for="mod in outcome.attribute_modifiers"
            :key="mod.attribute"
            class="mod-row"
          >
            <span class="attr-name">{{ mod.attribute.replace(/_/g, ' ') }}</span>
            <span class="mod-val" :class="mod.delta > 0 ? 'positive' : 'negative'">
              {{ mod.delta > 0 ? '+' : '' }}{{ mod.delta }}
            </span>
          </div>
        </div>

        <div class="features" v-if="outcome.features_granted?.length > 0">
          <div class="effects-label">Features Gained</div>
          <div v-for="f in outcome.features_granted" :key="f.id" class="feature-row">
            <span class="feature-name">{{ f.name }}</span>
            <span class="feature-desc">{{ f.description }}</span>
          </div>
        </div>
      </div>

      <button class="primary dismiss-btn" @click="emit('dismissed')">
        {{ sessionComplete ? 'View Character Sheet' : 'Continue' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.outcome-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 2rem;
}

.outcome-card {
  background: var(--color-surface);
  border-radius: var(--radius);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.outcome-badge {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

p {
  color: var(--color-text-muted);
  margin-bottom: 1.5rem;
}

.effects {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.effects-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.4rem;
}

.mod-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95rem;
}

.attr-name {
  text-transform: capitalize;
}

.mod-val {
  font-weight: 700;
  font-size: 1.1rem;
}

.positive {
  color: var(--color-success);
}

.negative {
  color: var(--color-danger);
}

.feature-row {
  margin-bottom: 0.5rem;
}

.feature-name {
  font-weight: 600;
  display: block;
  font-size: 0.95rem;
}

.feature-desc {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.dismiss-btn {
  width: 100%;
}
</style>
