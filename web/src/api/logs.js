import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
});

export const getLogs = async (params) => {
  const response = await api.get('/logs', { params });
  return response.data;
};
