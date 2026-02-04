<template>
  <div ref="artRef" class="w-full h-full rounded-xl overflow-hidden shadow-2xl bg-black"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Artplayer from 'artplayer'

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  style: {
    type: Object,
    default: () => ({}),
  },
})

const artRef = ref(null)
let instance = null

onMounted(() => {
  instance = new Artplayer({
    ...props.option,
    container: artRef.value,
    theme: '#6366f1', // Indigo-500
    icons: {
      state: '<svg width="72" height="72" viewBox="0 0 72 72"><path fill="#ffffff" d="M21.2,14.6c-2.3-1.3-5.2,0.3-5.2,3v36.8c0,2.6,2.9,4.3,5.2,3l32.1-18.4c2.3-1.3,2.3-4.7,0-6L21.2,14.6z"/></svg>',
    },
    setting: true,
    flip: true,
    playbackRate: true,
    aspectRatio: true,
    fullscreen: true,
    fullscreenWeb: true,
    miniProgressBar: true,
    mutex: true,
    backdrop: true,
    playsInline: true,
    autoPlayback: true,
    airplay: true,
    lock: true,
    fastForward: true,
    autoOrientation: true,
  })
})

onBeforeUnmount(() => {
  if (instance && instance.destroy) {
    instance.destroy(false)
  }
})

// Update src if it changes
watch(() => props.option.url, (newUrl) => {
    if (instance && newUrl) {
        instance.switchUrl(newUrl)
    }
})
</script>

<style>
.art-video-player {
    z-index: 50;
}
</style>
