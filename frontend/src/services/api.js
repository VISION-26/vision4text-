import axios from 'axios';

// Same-origin by default in production. Set VITE_API_BASE_URL only for split local development.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const api = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

const clearStoredAuth = () => {
    ['visiontext_access_token', 'visiontext_refresh_token', 'visiontext_user'].forEach((key) => localStorage.removeItem(key));
};

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('visiontext_access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

let refreshPromise = null;

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config || {};
        const status = error.response?.status;
        const isAuthRoute = String(original?.url || '').includes('/auth/login') || String(original?.url || '').includes('/auth/refresh');

        if (status === 401 && !original._evtRetried && !isAuthRoute) {
            const refreshToken = localStorage.getItem('visiontext_refresh_token');
            if (refreshToken) {
                original._evtRetried = true;
                try {
                    if (!refreshPromise) {
                        refreshPromise = axios
                            .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken }, { timeout: 30000 })
                            .then(({ data }) => {
                                localStorage.setItem('visiontext_access_token', data.access_token);
                                localStorage.setItem('visiontext_refresh_token', data.refresh_token);
                                if (data.user) {
                                    const normalized = { ...data.user, name: data.user.full_name || data.user.email };
                                    localStorage.setItem('visiontext_user', JSON.stringify(normalized));
                                }
                                return data.access_token;
                            })
                            .finally(() => { refreshPromise = null; });
                    }
                    const nextToken = await refreshPromise;
                    original.headers = original.headers || {};
                    original.headers.Authorization = `Bearer ${nextToken}`;
                    return api.request(original);
                } catch {
                    clearStoredAuth();
                    if (!window.location.pathname.startsWith('/login')) {
                        window.location.replace('/login?session=expired');
                    }
                    return Promise.reject(new Error('Your session expired. Please sign in again.'));
                }
            }

            clearStoredAuth();
            if (!window.location.pathname.startsWith('/login')) {
                window.location.replace('/login?session=expired');
            }
            return Promise.reject(new Error('Your session expired. Please sign in again.'));
        }

        const detail = error.response?.data?.detail;
        const message = typeof detail === 'string' ? detail : (error.message || 'API request failed');
        return Promise.reject(new Error(message));
    },
);

export default api;
