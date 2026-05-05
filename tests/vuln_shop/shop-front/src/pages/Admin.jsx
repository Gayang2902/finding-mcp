/**
 * src/pages/Admin.jsx
 *
 * VULN-F4: 클라이언트 역할 검사만으로 관리자 페이지 접근 제어
 *   useAuth()의 user.role이 "admin"인지만 확인.
 *   localStorage.setItem("user", JSON.stringify({...기존값, role:"admin"}))
 *   입력 후 새로고침 시 관리자 UI 진입 가능.
 *   (실제 API 호출 시엔 서버의 JWT 검증 존재하나 BUG-7 alg=none과 결합하면 완전 우회)
 */

import { useEffect, useState } from "react";
import { getAdminUsers } from "../api";
import { useAuth } from "../AuthContext";
import { useNavigate } from "react-router-dom";

export default function Admin() {
  const { user }    = useAuth();
  const navigate    = useNavigate();
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");

  // VULN-F4: 서버 검증 없이 클라이언트 role만 확인
  useEffect(() => {
    if (!user || user.role !== "admin") {
      navigate("/");
      return;
    }
    getAdminUsers()
      .then(setUsers)
      .catch(e => setError(e.response?.data?.detail || "접근 거부"));
  }, [user]);

  if (!user || user.role !== "admin") return null;

  return (
    <div style={styles.page}>
      <h2>관리자 — 사용자 목록</h2>
      {error && <p style={{ color:"#dc2626" }}>{error}</p>}
      <table style={styles.table}>
        <thead>
          <tr>{["ID","아이디","잔액","역할"].map(h =>
            <th key={h} style={styles.th}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id}>
              <td style={styles.td}>{u.id}</td>
              <td style={styles.td}>{u.username}</td>
              <td style={styles.td}>${u.balance?.toFixed(2)}</td>
              <td style={styles.td}>
                <span style={{
                  ...styles.badge,
                  background: u.role === "admin" ? "#fef3c7" : "#eff6ff",
                  color:      u.role === "admin" ? "#d97706" : "#2563eb",
                }}>{u.role}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  page:  { padding:"1.5rem" },
  table: { width:"100%", borderCollapse:"collapse", marginTop:16 },
  th:    { textAlign:"left", padding:"8px 12px", background:"#f9fafb",
           borderBottom:"1px solid #e5e7eb", fontSize:13, fontWeight:500 },
  td:    { padding:"8px 12px", borderBottom:"1px solid #f3f4f6", fontSize:13 },
  badge: { fontSize:11, padding:"2px 8px", borderRadius:99, fontWeight:500 },
};
