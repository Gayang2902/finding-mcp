import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import Navbar    from "./components/Navbar";
import Login     from "./pages/Login";
import Register  from "./pages/Register";
import Products  from "./pages/Products";
import Orders    from "./pages/Orders";
import Admin     from "./pages/Admin";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/"         element={<Navigate to="/products" />} />
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/products" element={<Products />} />
          <Route path="/orders"   element={<Orders />} />
          <Route path="/admin"    element={<Admin />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
