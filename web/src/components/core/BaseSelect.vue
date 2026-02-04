<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  options: {
    type: Array,
    required: true,
  },
  placeholder: {
    type: String,
    default: "请选择",
  },
});

const emit = defineEmits(["update:modelValue"]);

const isOpen = ref(false);
const dropdownRef = ref(null);

const selectedOption = computed(() => {
  return props.options.find((opt) => opt.value === props.modelValue);
});

const selectOption = (option) => {
  emit("update:modelValue", option.value);
  isOpen.value = false;
};

const toggleDropdown = () => {
  isOpen.value = !isOpen.value;
};

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<template>
  <div class="relative" ref="dropdownRef">
    <!-- Selected Value Display -->
    <button
      type="button"
      @click="toggleDropdown"
      class="block w-full rounded-2xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 sm:text-base py-3.5 pl-5 pr-12 transition-all shadow-inner cursor-pointer hover:bg-slate-100/50 dark:hover:bg-black/30 text-left"
    >
      <span v-if="selectedOption">{{ selectedOption.label }}</span>
      <span v-else class="text-slate-400">{{ placeholder }}</span>
    </button>

    <!-- Arrow Icon -->
    <div
      class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4"
    >
      <svg
        class="h-5 w-5 text-slate-400 dark:text-slate-500 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </div>

    <!-- Dropdown Options -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-show="isOpen"
        class="absolute z-10 mt-2 w-full rounded-2xl bg-white dark:bg-slate-800 shadow-2xl ring-1 ring-black ring-opacity-5 overflow-hidden"
      >
        <div class="py-2 max-h-60 overflow-auto custom-scrollbar">
          <button
            v-for="option in options"
            :key="option.value"
            type="button"
            @click="selectOption(option)"
            class="w-full text-left px-5 py-3 text-sm font-medium transition-colors duration-150"
            :class="[
              option.value === modelValue
                ? 'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-700 dark:text-cyan-300'
                : 'text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50',
            ]"
          >
            <div class="flex items-center justify-between">
              <span>{{ option.label }}</span>
              <svg
                v-if="option.value === modelValue"
                class="h-5 w-5 text-cyan-600 dark:text-cyan-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.3);
  border-radius: 20px;
}
</style>
