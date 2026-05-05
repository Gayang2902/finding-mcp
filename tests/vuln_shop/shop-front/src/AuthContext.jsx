/**
 * src/AuthContext.jsx
 *
 * VULN-F4: 클라이언트 사이드 역할(role) 검사만으로 관리자 UI 노출
 *   JWT 페이로드를 서버 검증 없이 디코딩해 role을 판단.
 *   브라우저 콘솔에서 localStorage.setItem("user", JSON.stringify({role:"admin"}))
 *   입력만으로 관리자 메뉴 노출됨.
 */

import { createContext, useContext, useState, useEffect } from "react";
import { getToken, getUser, saveUser, clearToken } from "./api";

const AuthContext = createContext(null);

function parseJwtPayload(token) {
  try {
    // VULN-F4: 서버 검증 없이 클라이언트에서 JWT 페이로드 파싱
    const base64 = token.split(".")[1];
    const json = atob(base64.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return {};
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = getToken();
    if (token) {
      const payload = parseJwtPayload(token);
      const stored  = getUser();
      setUser({ ...stored, ...payload });
    }
  }, []);

  function logout() {
    clearToken();
    localStorage.removeItem("user");
    setUser(null);
  }

  function setLoggedIn(data, userData) {
    const payload = parseJwtPayload(data.access_token);
    const merged  = { ...userData, ...payload };
    saveUser(merged);
    setUser(merged);
  }

  return (
    <AuthContext.Provider value={{ user, setLoggedIn, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
