import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
});

export const fetchParties = () => api.get("/mps/parties").then((res) => res.data);
export const fetchStates = () => api.get("/mps/states").then((res) => res.data);
export const fetchMPs = (params) => api.get("/mps", { params }).then((res) => res.data);
export const fetchMP = (slug) => api.get(`/mps/${slug}`).then((res) => res.data);
export const fetchStatsSummary = () => api.get("/mps/stats/summary").then((res) => res.data);
export const fetchFreshness = () => api.get("/mps/freshness").then((res) => res.data);
export const runPipeline = (payload) => api.post("/pipeline/run", payload).then((res) => res.data);
export const fetchPipelineStatus = (run_id) => api.get(`/pipeline/status/${run_id}`).then((res) => res.data);
export const fetchIntegrity = (slug) => api.get(`/integrity/${slug}`).then((res) => res.data);
export const fetchIntegritySummary = () => api.get("/integrity/summary").then((res) => res.data);
export const fetchStatements = (slug, params) => api.get(`/statements/${slug}`, { params }).then((res) => res.data);
export const fetchStatementsSummary = () => api.get("/statements/summary").then((res) => res.data);
export const submitDiscrepancyReport = (slug, payload) => api.post(`/reports/${slug}`, payload).then((res) => res.data);
export const fetchDiscrepancyReports = (params) => api.get("/reports", { params }).then((res) => res.data);

export default api;
