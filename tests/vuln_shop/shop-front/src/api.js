/**
 * src/api.js
 *
 * VULN-F1: JWT를 localStorage에 저장
 *   XSS 공격으로 document.cookie 대신 localStorage에서 토큰 탈취 가능.
 *   HttpOnly 쿠키에 비해 JS에서 직접 접근 가능.
 *
 * VULN-F2: 인증 정보 console.log 노출
 *   로그인 응답(토큰 포함)을 콘솔에 그대로 출력.
 *   개발자 도구 열린 상태에서 누구나 확인 가능.
 */

import axios from "axios";

const BASE = "http://localhost:8000";

// VULN-F1: localStorage에 토큰 저장
export const saveToken  = (token) => localStorage.setItem("token", token);
export const getToken   = ()      => localStorage.getItem("token");
export const clearToken = ()      => localStorage.removeItem("token");

export const saveUser   = (user)  => localStorage.setItem("user", JSON.stringify(user));
export const getUser    = ()      => JSON.parse(localStorage.getItem("user") || "null");

const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export async function login(username, password) {
  const form = new URLSearchParams({ username, password });
  const res = await api.post("/auth/login", form);

  // VULN-F2: 토큰 콘솔 노출
  console.log("[DEBUG] login response:", res.data);

  saveToken(res.data.access_token);
  return res.data;
}

export async function register(username, email, password, referral_code = "") {
  const res = await api.post("/auth/register", { username, email, password, referral_code });
  return res.data;
}

// Products
export async function getProducts() {
  const res = await api.get("/products");
  return res.data;
}

// Orders
export async function placeOrder(items, coupon_codes = []) {
  const res = await api.post("/orders/", { items, coupon_codes });
  return res.data;
}

// VULN-F3: 클라이언트가 total을 직접 지정 (BUG-6 프론트 노출)
export async function quickOrder(items, total) {
  const res = await api.post("/orders/quick", { items, total });
  return res.data;
}

export async function getOrders() {
  const res = await api.get("/orders/");
  return res.data;
}

export async function cancelOrder(orderId) {
  const res = await api.post(`/orders/${orderId}/cancel`);
  return res.data;
}

// Admin
export async function getAdminUsers() {
  const res = await api.get("/admin/users");
  return res.data;
}
