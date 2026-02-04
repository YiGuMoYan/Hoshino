console.log("%c [HOSHINO] APP STARTED - BUILD VERIFICATION " + Date.now(), "background: #222; color: #bada55; font-size: 20px");
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'

const pinia = createPinia()

createApp(App)
    .use(router)
    .use(pinia)
    .mount('#app')
