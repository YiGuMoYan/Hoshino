import { createRouter, createWebHistory } from 'vue-router'
// Views will be created soon
import Scan from '../views/Scan.vue'
import Settings from '../views/Settings.vue'
import Download from '../views/Download.vue'
import Subscription from '../views/Subscription.vue'
import LibraryView from '../views/LibraryView.vue'
import Logs from '../views/Logs.vue'

const routes = [
    { path: '/', redirect: '/scan' },
    { path: '/library', component: LibraryView, name: 'Library' },
    { path: '/scan', component: Scan, name: 'Scan' },
    { path: '/download', component: Download, name: 'Download' },
    { path: '/subscription', component: Subscription, name: 'Subscription' },
    { path: '/settings', component: Settings, name: 'Settings' },
    { path: '/logs', component: Logs, name: 'Logs' },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
