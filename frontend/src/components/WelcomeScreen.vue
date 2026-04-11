<script setup>
defineEmits(['start'])
</script>

<template>
  <div>
    <h1>Lifepaths</h1>
    <p>Create a character by rolling characteristics and choosing background skills.</p>
    <button @click="$emit('start')">Begin Character Creation</button>
  </div>
</template>
