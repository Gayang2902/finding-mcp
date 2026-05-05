import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav style={styles.nav}>
      <Link to="/" style={styles.brand}>🛒 vuln_shop</Link>
      <div style={styles.links}>
        <Link to="/products" style={styles.link}>상품</Link>
        {user && <Link to="/orders" style={styles.link}>주문</Link>}
        {/* VULN-F4: 클라이언트 role 기반 관리자 메뉴 노출 */}
        {user?.role === "admin" && (
          <Link to="/admin" style={{ ...styles.link, color:"#d97706" }}>관리자</Link>
        )}
        {user
          ? <button onClick={handleLogout} style={styles.logoutBtn}>
              {user.username} 로그아웃
            </button>
          : <Link to="/login" style={styles.link}>로그인</Link>
        }
      </div>
    </nav>
  );
}

const styles = {
  nav:       { display:"flex", alignItems:"center", justifyContent:"space-between",
               padding:"0 1.5rem", height:52, background:"#fff",
               borderBottom:"1px solid #e5e7eb", position:"sticky", top:0, zIndex:10 },
  brand:     { fontWeight:700, fontSize:16, textDecoration:"none", color:"#111" },
  links:     { display:"flex", alignItems:"center", gap:16 },
  link:      { fontSize:14, textDecoration:"none", color:"#374151" },
  logoutBtn: { fontSize:13, background:"none", border:"none", cursor:"pointer",
               color:"#6b7280", padding:0 },
};
