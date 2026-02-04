
import request from '@/utils/request';

// Search
export const searchMikan = (keyword) => request.post('/subscription/search', { keyword });

export const getBangumiDetail = (mikanId) => request.get(`/subscription/bangumi/${mikanId}`);

// Subscription CRUD
export const createSubscription = (data) => request.post('/subscription/', data);

export const listSubscriptions = () => request.get('/subscription/');

export const getSubscription = (id) => request.get(`/subscription/${id}`);

export const updateSubscription = (id, data) => request.put(`/subscription/${id}`, data);

export const deleteSubscription = (id, delete_files = false) => request.delete(`/subscription/${id}`, { params: { delete_files } });

// Actions
export const pauseSubscription = (id) => request.post(`/subscription/${id}/pause`);

export const resumeSubscription = (id) => request.post(`/subscription/${id}/resume`);

export const checkSubscription = (id) => request.post(`/subscription/${id}/check`);

export const getSubscriptionItems = (id) => request.get(`/subscription/${id}/items`);
