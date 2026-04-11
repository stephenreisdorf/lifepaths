<script setup>
defineProps({
  characteristics: Object,
})

function formatModifier(m) {
  return m >= 0 ? '+' + m : String(m)
}
</script>

<template>
  <table>
    <thead>
      <tr><th>Attribute</th><th>Value</th><th>DM</th></tr>
    </thead>
    <tbody>
      <tr v-for="(info, name) in characteristics" :key="name">
        <td>{{ name }}</td>
        <td class="mono">{{ info.value }}</td>
        <td class="mono">{{ formatModifier(info.modifier) }}</td>
      </tr>
    </tbody>
  </table>
</template>
