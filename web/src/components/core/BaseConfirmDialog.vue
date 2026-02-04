<script setup>
defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  title: {
    type: String,
    default: "确认操作",
  },
  message: {
    type: String,
    default: "",
  },
  confirmText: {
    type: String,
    default: "确认执行",
  },
  cancelText: {
    type: String,
    default: "取消",
  },
  confirmButtonClass: {
    type: String,
    default: "bg-rose-500 hover:bg-rose-600 shadow-rose-500/20",
  },
});

const emit = defineEmits(["update:show", "confirm", "cancel"]);

const close = () => {
  emit("update:show", false);
  emit("cancel");
};

const handleConfirm = () => {
  emit("confirm");
  emit("update:show", false);
};
</script>

<template>
  <transition name="fade">
    <div
      v-if="show"
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
    >
      <div
        class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 max-w-md w-full border border-white/20 transform transition-all scale-100"
      >
        <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-3">
          {{ title }}
        </h3>
        <p
          class="text-slate-600 dark:text-slate-300 font-medium leading-relaxed"
        >
          {{ message }}
        </p>

        <!-- Custom Content Slot -->
        <slot />

        <div class="mt-8 flex justify-end gap-3">
          <button
            @click="close"
            class="px-5 py-2.5 rounded-xl font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            {{ cancelText }}
          </button>
          <button
            @click="handleConfirm"
            :class="confirmButtonClass"
            class="px-6 py-2.5 rounded-xl font-bold text-white shadow-lg active:scale-95 transition-all"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
