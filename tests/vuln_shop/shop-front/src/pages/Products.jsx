/**
 * src/pages/Products.jsx
 *
 * VULN-F6: XSS — 상품 설명을 dangerouslySetInnerHTML로 렌더링
 *   서버에서 내려온 product.description을 이스케이프 없이 HTML로 삽입.
 *   악의적인 상품 설명에 <script> 또는 <img onerror=...> 삽입 시 실행됨.
 *
 * VULN-F3: 클라이언트 사이드 가격 오버라이드
 *   "빠른 구매" 버튼은 사용자가 수정 가능한 price 필드를 total로 전송.
 *   브라우저 DevTools에서 state 변경 또는 입력 조작으로 임의 금액 결제 가능.
 */

import { useEffect, useState } from "react";
import { getProducts, quickOrder, placeOrder } from "../api";
import { useNavigate } from "react-router-dom";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [msg, setMsg]           = useState("");
  const [prices, setPrices]     = useState({});  // VULN-F3: 사용자 입력 가격
  const navigate                = useNavigate();

  useEffect(() => { getProducts().then(setProducts); }, []);

  // VULN-F3: total을 클라이언트 입력값으로 전송
  async function handleQuickBuy(product) {
    const total = parseFloat(prices[product.id] ?? product.price);
    try {
      await quickOrder([{ product_id: product.id, quantity: 1 }], total);
      setMsg(`"${product.name}" 구매 완료 ($${total})`);
      setTimeout(() => navigate("/orders"), 1000);
    } catch (e) {
      setMsg(e.response?.data?.detail || "오류 발생");
    }
  }

  async function handleNormalBuy(product) {
    try {
      await placeOrder([{ product_id: product.id, quantity: 1 }]);
      setMsg(`"${product.name}" 구매 완료`);
      setTimeout(() => navigate("/orders"), 1000);
    } catch (e) {
      setMsg(e.response?.data?.detail || "오류 발생");
    }
  }

  return (
    <div style={styles.page}>
      <h2>상품 목록</h2>
      {msg && <div style={styles.toast}>{msg}</div>}
      <div style={styles.grid}>
        {products.map(p => (
          <div key={p.id} style={styles.card}>
            <h3 style={{ marginBottom:4 }}>{p.name}</h3>

            {/* VULN-F6: XSS — description을 raw HTML로 삽입 */}
            {p.description && (
              <div
                style={{ fontSize:13, color:"#555", marginBottom:8 }}
                dangerouslySetInnerHTML={{ __html: p.description }}
              />
            )}

            <p style={styles.price}>${p.price}</p>
            <p style={{ fontSize:12, color:"#6b7280" }}>재고: {p.stock}</p>

            {/* VULN-F3: 결제 금액 직접 입력 */}
            <div style={{ marginTop:8, marginBottom:8 }}>
              <label style={{ fontSize:12, color:"#6b7280" }}>결제 금액 (빠른 구매용)</label>
              <input
                style={styles.priceInput}
                type="number"
                step="0.01"
                value={prices[p.id] ?? p.price}
                onChange={e => setPrices({ ...prices, [p.id]: e.target.value })}
              />
            </div>

            <div style={{ display:"flex", gap:8 }}>
              <button style={styles.btnPrimary} onClick={() => handleNormalBuy(p)}>
                구매
              </button>
              <button style={styles.btnSecondary} onClick={() => handleQuickBuy(p)}>
                빠른 구매
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  page:        { padding:"1.5rem" },
  grid:        { display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))", gap:16, marginTop:16 },
  card:        { background:"#fff", border:"1px solid #e5e7eb", borderRadius:10, padding:"1rem" },
  price:       { fontSize:18, fontWeight:600, color:"#2563eb", margin:"4px 0" },
  priceInput:  { display:"block", width:"100%", padding:"5px 8px", border:"1px solid #d1d5db",
                 borderRadius:5, fontSize:13, marginTop:4, boxSizing:"border-box" },
  btnPrimary:  { flex:1, padding:"7px 0", background:"#2563eb", color:"#fff",
                 border:"none", borderRadius:5, cursor:"pointer", fontSize:13 },
  btnSecondary:{ flex:1, padding:"7px 0", background:"#f3f4f6", color:"#111",
                 border:"1px solid #d1d5db", borderRadius:5, cursor:"pointer", fontSize:13 },
  toast:       { background:"#dcfce7", border:"1px solid #86efac", borderRadius:6,
                 padding:"8px 12px", marginBottom:12, fontSize:13 },
};
