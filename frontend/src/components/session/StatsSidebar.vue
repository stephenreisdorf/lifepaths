<script setup>
defineProps({
  sessionState: Object,
  characterName: String,
})
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-section" v-if="characterName">
      <div class="char-name">{{ characterName }}</div>
      <div class="age-line" v-if="sessionState">Age {{ sessionState.current_age }}</div>
    </div>
    <div class="sidebar-section" v-else-if="sessionState">
      <div class="age-line">Age {{ sessionState.current_age }}</div>
    </div>

    <div class="sidebar-section" v-if="sessionState">
      <h3>Attributes</h3>
      <dl class="attr-list">
        <div
          v-for="(val, attr) in sessionState.current_attributes"
          :key="attr"
          class="attr-row"
        >
          <dt>{{ attr.replace(/_/g, ' ') }}</dt>
          <dd>{{ val }}</dd>
        </div>
      </dl>
    </div>

    <div
      class="sidebar-section"
      v-if="sessionState && sessionState.current_features.length > 0"
    >
      <h3>Features</h3>
      <ul class="feature-list">
        <li v-for="f in sessionState.current_features" :key="f.id">
          <span class="feature-name">{{ f.name }}</span>
          <span v-if="f.category" class="feature-cat">{{ f.category }}</span>
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem;
}

.sidebar-section {
  margin-bottom: 1.5rem;
}

.sidebar-section:last-child {
  margin-bottom: 0;
}

.char-name {
  font-weight: 700;
  font-size: 1.1rem;
}

.age-line {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-top: 0.15rem;
}

h3 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.attr-list {
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.attr-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.95rem;
}

dt {
  text-transform: capitalize;
}

dd {
  margin: 0;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.feature-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.feature-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.feature-name {
  color: var(--color-text);
}

.feature-cat {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: capitalize;
  background: var(--color-surface-raised);
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
}
</style>
