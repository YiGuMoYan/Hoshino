import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0

export function useToast() {
  const add = (type, text, duration = 3000) => {
    const id = idCounter++
    const toast = { id, type, text }
    console.log('[useToast] Adding toast:', toast)
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }
  }

  const remove = (id) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  const success = (text, duration) => add('success', text, duration)
  const error = (text, duration) => add('error', text, duration)
  const info = (text, duration) => add('info', text, duration)
  const warning = (text, duration) => add('warning', text, duration)

  return {
    toasts,
    add,
    remove,
    success,
    error,
    info,
    warning
  }
}
