/**
 * src/pages/Orders.jsx
 *
 * VULN-F7: IDOR — 취소 요청 시 order_id를 클라이언트가 직접 입력 가능
 *   UI에서 자신의 주문만 보여주지만, "직접 입력 취소" 필드에서
 *   다른 사용자의 order_id를 입력하면 서버가 소유권 확인을 하지 않는
 *   BUG-5와 결합해 타인 주문 취소 + 중복 환불 가능.
 *   (실제로는 서버가 user_id 체크를 하지만 UI가 다른 ID 시도를 허용함)
 */

import { useEffect, useState } from "react";
import { getOrders, cancelOrder } from "../api";

export default function Orders() {
  const [orders, setOrders]   = useState([]);
  const [manualId, setManualId] = useState("");  // VULN-F7
  const [msg, setMsg]         = useState("");

  useEffect(() => { getOrders().then(setOrders); }, []);

  async function handleCancel(id) {
    try {
      const res = await cancelOrder(id);
      setMsg(`주문 #${id} 취소 완료 | 환불: $${res.refunded} | 잔액: $${res.balance}`);
      setOrders(prev => prev.map(o => o.id === id ? { ...o, status: "cancelled" } : o));
    } catch (e) {
      setMsg(e.response?.data?.detail || "오류");
    }
  }

  const statusColor = { paid:"#2563eb", shipped:"#16a34a", cancelled:"#dc2626", pending:"#d97706" };

  return (
    <div style={styles.page}>
      <h2>내 주문</h2>
      {msg && <div style={styles.toast}>{msg}</div>}

      {orders.length === 0
        ? <p style={{ color:"#6b7280" }}>주문 내역이 없습니다.</p>
        : orders.map(o => (
          <div key={o.id} style={styles.row}>
            <div>
              <span style={styles.orderId}>주문 #{o.id}</span>
              <span style={{ ...styles.badge, background: statusColor[o.status]+"22",
                color: statusColor[o.status] }}>{o.status}</span>
            </div>
            <div style={styles.total}>${o.total?.toFixed(2)}</div>
            {o.status === "paid" && (
              <button style={styles.btnCancel} onClick={() => handleCancel(o.id)}>
                취소
              </button>
            )}
            {/* VULN-F7: BUG-5와 연계 — 이미 취소된 주문도 버튼 노출 */}
            {o.status === "cancelled" && (
              <button style={{ ...styles.btnCancel, opacity:0.6 }}
                onClick={() => handleCancel(o.id)}>
                재취소 (중복 환불 테스트)
              </button>
            )}
          </div>
        ))
      }

      {/* VULN-F7: 임의 order_id로 취소 요청 */}
      <div style={styles.manualBox}>
        <h4 style={{ marginBottom:8 }}>직접 주문 ID로 취소</h4>
        <div style={{ display:"flex", gap:8 }}>
          <input style={styles.input} placeholder="Order ID"
            value={manualId} onChange={e => setManualId(e.target.value)} />
          <button style={styles.btnPrimary} onClick={() => handleCancel(Number(manualId))}>
            취소 요청
          </button>
        </div>
        <p style={{ fontSize:11, color:"#9ca3af", marginTop:4 }}>
          타인의 order_id 입력 시 IDOR 테스트 가능
        </p>
      </div>
    </div>
  );
}

const styles = {
  page:      { padding:"1.5rem" },
  row:       { display:"flex", alignItems:"center", gap:12, background:"#fff",
               border:"1px solid #e5e7eb", borderRadius:8, padding:"12px 16px", marginBottom:8 },
  orderId:   { fontWeight:500, marginRight:8 },
  badge:     { fontSize:11, padding:"2px 8px", borderRadius:99, fontWeight:500 },
  total:     { marginLeft:"auto", fontWeight:600 },
  btnCancel: { padding:"5px 12px", background:"#fef2f2", color:"#dc2626",
               border:"1px solid #fca5a5", borderRadius:5, cursor:"pointer", fontSize:12 },
  toast:     { background:"#dcfce7", border:"1px solid #86efac", borderRadius:6,
               padding:"8px 12px", marginBottom:12, fontSize:13 },
  manualBox: { marginTop:24, padding:16, background:"#fffbeb", border:"1px solid #fcd34d",
               borderRadius:8 },
  input:     { padding:"6px 10px", border:"1px solid #d1d5db", borderRadius:5,
               fontSize:13, width:120 },
  btnPrimary:{ padding:"6px 14px", background:"#2563eb", color:"#fff",
               border:"none", borderRadius:5, cursor:"pointer", fontSize:13 },
};
