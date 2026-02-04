<script setup>
import { useToast } from '@/composables/useToast'


const { toasts, remove } = useToast()
console.log('[ToastContainer] Mounted. Current toasts:', toasts.value)
</script>

<template>
  <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-md transition-all duration-300 min-w-[300px] max-w-md"
        :class="{
          'bg-emerald-50/90 dark:bg-emerald-900/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-100': toast.type === 'success',
          'bg-rose-50/90 dark:bg-rose-900/40 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-100': toast.type === 'error',
          'bg-sky-50/90 dark:bg-sky-900/40 border-sky-200 dark:border-sky-800 text-sky-800 dark:text-sky-100': toast.type === 'info',
          'bg-amber-50/90 dark:bg-amber-900/40 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-100': toast.type === 'warning',
        }"
      >
        <!-- Icon -->
        <div class="flex-shrink-0">
          <svg v-if="toast.type === 'success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
          <svg v-if="toast.type === 'error'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <svg v-if="toast.type === 'info'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <svg v-if="toast.type === 'warning'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
        </div>

        <!-- Text -->
        <div class="text-sm font-bold flex-1">{{ toast.text }}</div>

        <!-- Close -->
        <button @click="remove(toast.id)" class="opacity-50 hover:opacity-100 transition-opacity">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(30px) scale(0.9);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(30px) scale(0.9);
}
</style>
