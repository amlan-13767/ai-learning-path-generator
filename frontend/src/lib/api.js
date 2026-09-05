import axios from 'axios';

/**
 * Base URL for every API call.
 *
 * Empty by default, which means "same origin". In development the Vite dev
 * server proxies /api, /auth and /health straight through to Flask, so the
 * browser only ever talks to port 3000 and the Flask session cookie stays
 * first-party. Set VITE_API_URL to an absolute URL only for a split deployment
 * where CORS and SameSite=None; Secure cookies have been configured.
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';

const api = axios.create({
  baseURL: API_BASE_URL,
  // Send the Flask session cookie with every request. This is what restores the
  // logged-in user after a page refresh.
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * The API answers unauthenticated calls with JSON 401 (never an HTML redirect
 * to a Flask login page). Surface that as a normal rejected promise so callers
 * can route to the React /login page themselves.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      error.isUnauthenticated = true;
    }
    return Promise.reject(error);
  },
);

export const loginRequired = (error) => Boolean(error?.isUnauthenticated);

/**
 * Generate a new learning path
 * @param {Object} data - Learning path parameters
 * @returns {Promise<{task_id: string, status: string, message: string}>}
 */
export const generateLearningPath = async (data) => {
  const response = await api.post('/api/generate', data);
  return response.data;
};

/**
 * Check the status of a task
 * @param {string} taskId - Task ID
 * @returns {Promise<{status: string, progress?: number, message?: string}>}
 */
export const checkTaskStatus = async (taskId) => {
  const response = await api.get(`/api/status/${taskId}`);
  return response.data;
};

/**
 * Get the result of a completed task
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} - Learning path data
 */
export const getTaskResult = async (taskId) => {
  const response = await api.get(`/api/result/${taskId}`);
  return response.data;
};

/**
 * Check API health
 * @returns {Promise<{status: string}>}
 */
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/api/me');
  return response.data;
};

export const getUserPaths = async () => {
  const response = await api.get('/api/paths');
  return response.data;
};

export const getUserPath = async (pathId) => {
  const response = await api.get(`/api/paths/${pathId}`);
  return response.data;
};

/**
 * Save the full learning path for the logged-in user.
 * @param {Object} path - The full LearningPath JSON
 * @returns {Promise<{success: boolean, path_id: string}>}
 */
export const saveLearningPath = async (path) => {
  const response = await api.post('/api/save-path', { path });
  return response.data;
};

/**
 * Toggle milestone completion for a saved path.
 * @param {string} pathId
 * @param {number} milestoneIndex
 * @param {boolean} completed
 * @returns {Promise<{success: boolean}>}
 */
export const trackMilestone = async (pathId, milestoneIndex, completed) => {
  const response = await api.post('/api/track-milestone', {
    path_id: pathId,
    milestone_index: milestoneIndex,
    completed,
  });
  return response.data;
};

export const askQuestion = async (question, pathId) => {
  const response = await api.post('/api/ask', { question, path_id: pathId });
  return response.data;
};

export default api;
