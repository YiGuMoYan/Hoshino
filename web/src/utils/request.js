import axios from 'axios'

// Create axios instance
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000 // Default timeout: 10s
})

// Request interceptor
service.interceptors.request.use(
    config => {
        // Set no timeout for scan endpoint (LLM + TMDB analysis can take time)
        if (config.url && (
            (config.url.includes('/scan') && config.url.includes('/execute')) ||
            config.url.includes('/library/scan') ||
            config.url.includes('/downloads/preview') ||
            config.url.includes('/subscription/search') ||
            config.url.includes('/api/subscription/bangumi/')
        )) {
            config.timeout = 0 // No timeout for scan operations and preview
        }
        return config
    },
    error => {
        // do something with request error
        console.log(error) // for debug
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        console.log('err' + error) // for debug
        // You can add global error handling here (e.g., toast notifications)
        return Promise.reject(error)
    }
)

export default service
