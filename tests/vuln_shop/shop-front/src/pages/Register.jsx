import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../api";

export default function Register() {
  const [form, setForm]   = useState({ username:"", email:"", password:"", referral_code:"" });
  const [error, setError] = useState("");
  const navigate          = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await register(form.username, form.email, form.password, form.referral_code);
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "회원가입 실패");
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h2 style={styles.title}>회원가입</h2>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          {[["username","아이디"],["email","이메일"],["password","비밀번호","password"],
            ["referral_code","추천인 코드 (선택)"]].map(([k,ph,type]) => (
            <input key={k} style={styles.input} placeholder={ph} type={type||"text"}
              value={form[k]} onChange={set(k)} />
          ))}
          <button style={styles.btn} type="submit">가입하기</button>
        </form>
        <p style={{ marginTop:12, fontSize:13 }}>
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
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
