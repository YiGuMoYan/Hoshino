import request from '@/utils/request'

// 任务管理
export function listTasks(skip = 0, limit = 50) {
    return request({
        url: '/tasks',
        method: 'get',
        params: { skip, limit }
    })
}

export function getTask(taskId) {
    return request({
        url: `/tasks/${taskId}`,
        method: 'get'
    })
}

export function deleteTask(taskId) {
    return request({
        url: `/tasks/${taskId}`,
        method: 'delete'
    })
}

// 任务操作
export function scanDirectory(path) {
    return request({
        url: '/scan',
        method: 'post',
        data: { directory_path: path }
    })
}

export function executeTaskPlan(taskId) {
    return request({
        url: `/tasks/${taskId}/execute`,
        method: 'post'
    })
}

export function rollbackTask(taskId) {
    return request({
        url: `/tasks/${taskId}/rollback`,
        method: 'post'
    })
}

// 兼容旧的 API（用于 execute/rollback 路由）
export function executePlan(plan) {
    return request({
        url: '/scan/execute',
        method: 'post',
        data: plan
    })
}

export function rollbackPlan() {
    return request({
        url: '/scan/rollback',
        method: 'post'
    })
}
