import { ref, watchEffect } from 'vue'

const isDark = ref(localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches))

export function useDark() {
    watchEffect(() => {
        const html = document.documentElement
        if (isDark.value) {
            html.classList.add('dark')
            localStorage.setItem('theme', 'dark')
        } else {
            html.classList.remove('dark')
            localStorage.setItem('theme', 'light')
        }
    })

    const toggleDark = () => {
        isDark.value = !isDark.value
    }

    return { isDark, toggleDark }
}
