<script setup>
import { reactive, computed } from 'vue'
import StatsTable from './StatsTable.vue'
import SkillGrid from './SkillGrid.vue'

const props = defineProps({
  characteristics: Object,
  skillOptions: Array,
  requiredSkillCount: Number,
  error: String,
})

const emit = defineEmits(['confirm'])

const selected = reactive(new Set())

function toggleSkill(skill) {
  if (selected.has(skill)) {
    selected.delete(skill)
  } else {
    selected.add(skill)
  }
}

const canConfirm = computed(() => selected.size === props.requiredSkillCount)

function confirm() {
  emit('confirm', [...selected])
}
</script>

<template>
  <div>
    <h2>Characteristics</h2>
    <StatsTable :characteristics="characteristics" />

    <h2>Background Skills</h2>
    <p class="skill-counter">Select <span>{{ requiredSkillCount }}</span> skills:</p>
    <SkillGrid :skills="skillOptions" :selected="selected" @toggle="toggleSkill" />
    <p class="skill-counter"><span>{{ selected.size }}</span> / <span>{{ requiredSkillCount }}</span> selected</p>
    <p v-if="error" class="error">{{ error }}</p>
    <button :disabled="!canConfirm" @click="confirm">Confirm Skills</button>
  </div>
</template>
