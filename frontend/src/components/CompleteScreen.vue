<script setup>
import AttributeGrid from './complete/AttributeGrid.vue'
import FeatureList from './complete/FeatureList.vue'
import StageHistoryList from './complete/StageHistoryList.vue'

defineProps({
  characterSheet: Object,
  lifepathConfig: Object,
})
</script>

<template>
  <div class="complete-screen" v-if="characterSheet">
    <header class="sheet-header">
      <div class="title-block">
        <h1>{{ characterSheet.character_name ?? 'Your Character' }}</h1>
        <div class="meta-line" v-if="characterSheet.player_name">
          Player: {{ characterSheet.player_name }}
        </div>
        <div class="meta-line">
          Age {{ characterSheet.age }}<span v-if="lifepathConfig"> · {{ lifepathConfig.name }}</span>
        </div>
      </div>
    </header>

    <div class="sheet-body">
      <section class="sheet-section">
        <h2>Attributes</h2>
        <AttributeGrid :attributes="characterSheet.attributes" />
      </section>

      <section class="sheet-section">
        <h2>Features</h2>
        <FeatureList :features="characterSheet.features" />
      </section>

      <section class="sheet-section">
        <h2>Life History</h2>
        <StageHistoryList :stage-history="characterSheet.stage_history" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.complete-screen {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.sheet-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--color-border);
}

h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
}

.meta-line {
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.sheet-body {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.sheet-section h2 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}
</style>
