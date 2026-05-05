/**
 * src/pages/Login.jsx
 *
 * VULN-F5: 오픈 리다이렉트
 *   로그인 성공 후 ?redirect= 파라미터를 검증 없이 그대로 사용.
 *   /login?redirect=https://evil.com 으로 유도 가능.
 */

import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { login } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const [form, setForm]   = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate          = useNavigate();
  const [params]          = useSearchParams();
  const { setLoggedIn }   = useAuth();

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      const data = await login(form.username, form.password);
      setLoggedIn(data, { username: form.username });

      // VULN-F5: redirect 파라미터 검증 없이 사용
      const redirect = params.get("redirect") || "/";
      window.location.href = redirect;
    } catch {
      setError("로그인 실패");
    }
  }

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h2 style={styles.title}>로그인</h2>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input style={styles.input} placeholder="아이디"
            value={form.username}
            onChange={e => setForm({ ...form, username: e.target.value })} />
          <input style={styles.input} type="password" placeholder="비밀번호"
            value={form.password}
            onChange={e => setForm({ ...form, password: e.target.value })} />
          <button style={styles.btn} type="submit">로그인</button>
        </form>
        <p style={{ marginTop: 12, fontSize: 13 }}>
          계정이 없으신가요? <Link to="/register">회원가입</Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  wrap:  { display:"flex", justifyContent:"center", alignItems:"center", minHeight:"80vh" },
  card:  { background:"#fff", border:"1px solid #e5e7eb", borderRadius:12, padding:"2rem", width:320 },
  title: { marginBottom:16, fontSize:20 },
  input: { display:"block", width:"100%", marginBottom:10, padding:"8px 10px",
           border:"1px solid #d1d5db", borderRadius:6, fontSize:14, boxSizing:"border-box" },
  btn:   { width:"100%", padding:"9px 0", background:"#2563eb", color:"#fff",
           border:"none", borderRadius:6, cursor:"pointer", fontSize:14 },
  error: { color:"#dc2626", fontSize:13, marginBottom:8 },
};
