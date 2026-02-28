<script setup>
defineProps({
  attributes: Object,
})
</script>

<template>
  <div class="attribute-grid">
    <div v-for="(val, attr) in attributes" :key="attr" class="attr-cell">
      <div class="attr-val">{{ val }}</div>
      <div class="attr-name">{{ attr.replace(/_/g, ' ') }}</div>
    </div>
  </div>
</template>

<style scoped>
.attribute-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.attr-cell {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  text-align: center;
  min-width: 110px;
}

.attr-val {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.attr-name {
  font-size: 0.8rem;
  text-transform: capitalize;
  color: var(--color-text-muted);
}
</style>
