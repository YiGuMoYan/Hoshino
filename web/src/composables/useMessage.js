export function useMessage() {
  const createToast = (type, msg) => {
    // Basic toast implementation
    const div = document.createElement('div')
    // Styling: fixed top-right, z-index high, padding, rounded, shadow, animation
    div.className = `fixed top-4 right-4 z-[9999] px-4 py-3 rounded-lg shadow-xl text-white transform transition-all duration-300 translate-x-full opacity-0 flex items-center gap-2 min-w-[300px]`
    
    // Icon and Color based on type
    let icon = ''
    if (type === 'success') {
      div.classList.add('bg-green-600')
      icon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`
    } else if (type === 'error') {
      div.classList.add('bg-red-600')
      icon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`
    } else if (type === 'warning') {
      div.classList.add('bg-yellow-500')
      icon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>`
    } else {
      div.classList.add('bg-blue-600')
      icon = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`
    }

    div.innerHTML = `${icon} <span class="font-medium">${msg}</span>`

    // Append to body
    document.body.appendChild(div)

    // Trigger animation
    requestAnimationFrame(() => {
      div.classList.remove('translate-x-full', 'opacity-0')
    })

    // Auto remove
    setTimeout(() => {
      div.classList.add('translate-x-full', 'opacity-0')
      setTimeout(() => {
        if (div.parentNode) document.body.removeChild(div)
      }, 300)
    }, 3000)
  }

  return {
    success: (msg) => createToast('success', msg),
    error: (msg) => createToast('error', msg),
    info: (msg) => createToast('info', msg),
    warning: (msg) => createToast('warning', msg)
  }
}
