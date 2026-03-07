import React, { useState, useEffect, createContext, useContext, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Scroll to top on new navigation, preserve position on back/forward
const ScrollToTop = () => {
  const location = useLocation();
  const isPopState = useRef(false);
  
  useEffect(() => {
    // Enable manual scroll restoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
    
    // Listen for popstate (back/forward)
    const handlePopState = () => {
      isPopState.current = true;
    };
    
    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);
  
  useEffect(() => {
    // Small delay to allow popstate to be detected
    const timer = setTimeout(() => {
      if (!isPopState.current) {
        // New navigation - scroll to top
        window.scrollTo(0, 0);
      }
      // Reset the flag
      isPopState.current = false;
    }, 10);
    
    return () => clearTimeout(timer);
  }, [location.pathname, location.search]);
  
  // Save scroll position before leaving page
  useEffect(() => {
    const saveScrollPos = () => {
      const key = location.pathname + location.search;
      sessionStorage.setItem(`scroll_${key}`, String(window.scrollY));
    };
    
    window.addEventListener('beforeunload', saveScrollPos);
    
    // Also save on route change
    return () => {
      saveScrollPos();
      window.removeEventListener('beforeunload', saveScrollPos);
    };
  }, [location.pathname, location.search]);
  
  // Restore scroll position for back/forward
  useEffect(() => {
    if (isPopState.current) {
      const key = location.pathname + location.search;
      const savedPos = sessionStorage.getItem(`scroll_${key}`);
      if (savedPos) {
        setTimeout(() => {
          window.scrollTo(0, parseInt(savedPos, 10));
        }, 50);
      }
    }
  }, [location.pathname, location.search]);
  
  return null;
};

// Pages
import HomePage from "./pages/HomePage";
import ProductsPage from "./pages/ProductsPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import CartPage from "./pages/CartPage";
import CheckoutSuccessPage from "./pages/CheckoutSuccessPage";
import AccountPage from "./pages/AccountPage";
import AdminDashboard from "./pages/AdminDashboard";
import AdminPromotionsPage from "./pages/AdminPromotionsPage";
import AdminProductsPage from "./pages/AdminProductsPage";
import AdminOrdersPage from "./pages/AdminOrdersPage";
import AdminAnalyticsPage from "./pages/AdminAnalyticsPage";
import AdminEmailAutomationPage from "./pages/AdminEmailAutomationPage";
import AdminCustomerSegmentsPage from "./pages/AdminCustomerSegmentsPage";
import AgentsPage from "./pages/AgentsPage";
import ReferralPage from "./pages/ReferralPage";
import SupportPage from "./pages/SupportPage";
import AdminSourcingPage from "./pages/AdminSourcingPage";
import WishlistPage from "./pages/WishlistPage";

// Components
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import AuthModal from "./components/AuthModal";
import CartDrawer from "./components/CartDrawer";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// Cart Context
const CartContext = createContext(null);
export const useCart = () => useContext(CartContext);

// Wishlist Context
const WishlistContext = createContext(null);
export const useWishlist = () => useContext(WishlistContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("calmtails_token"));

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem("calmtails_token");
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem("calmtails_token", newToken);
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name });
    const { token: newToken, user: userData, message } = response.data;
    localStorage.setItem("calmtails_token", newToken);
    setToken(newToken);
    setUser(userData);
    return { user: userData, message };
  };

  const logout = () => {
    localStorage.removeItem("calmtails_token");
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (token) {
      await fetchUser();
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshUser, API }}>
      {children}
    </AuthContext.Provider>
  );
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({ items: [], subtotal: 0, item_count: 0 });
  const [cartOpen, setCartOpen] = useState(false);
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem("calmtails_cart_session");
    if (existing) return existing;
    const newId = `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("calmtails_cart_session", newId);
    return newId;
  });

  useEffect(() => {
    fetchCart();
  }, [sessionId]);

  const fetchCart = async () => {
    try {
      const response = await axios.get(`${API}/cart/${sessionId}`);
      setCart(response.data);
    } catch (error) {
      console.error("Error fetching cart:", error);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    try {
      const response = await axios.post(`${API}/cart/${sessionId}/add`, {
        product_id: productId,
        quantity
      });
      setCart(response.data);
      setCartOpen(true);
      toast.success("Added to cart!");
      return response.data;
    } catch (error) {
      toast.error("Failed to add to cart");
      throw error;
    }
  };

  const updateQuantity = async (productId, quantity) => {
    try {
      const response = await axios.post(`${API}/cart/${sessionId}/update`, {
        product_id: productId,
        quantity
      });
      setCart(response.data);
      return response.data;
    } catch (error) {
      toast.error("Failed to update cart");
      throw error;
    }
  };

  const removeFromCart = async (productId) => {
    try {
      const response = await axios.delete(`${API}/cart/${sessionId}/item/${productId}`);
      setCart(response.data);
      toast.success("Removed from cart");
      return response.data;
    } catch (error) {
      toast.error("Failed to remove item");
      throw error;
    }
  };

  const clearCart = async () => {
    try {
      await axios.delete(`${API}/cart/${sessionId}`);
      setCart({ items: [], subtotal: 0, item_count: 0 });
    } catch (error) {
      console.error("Error clearing cart:", error);
    }
  };

  return (
    <CartContext.Provider value={{
      cart,
      cartOpen,
      setCartOpen,
      sessionId,
      addToCart,
      updateQuantity,
      removeFromCart,
      clearCart,
      fetchCart
    }}>
      {children}
    </CartContext.Provider>
  );
};

export const WishlistProvider = ({ children }) => {
  const { user, token } = useAuth();
  const [wishlist, setWishlist] = useState({ items: [], count: 0 });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && token) {
      fetchWishlist();
    } else {
      setWishlist({ items: [], count: 0 });
    }
  }, [user, token]);

  const fetchWishlist = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/wishlist`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setWishlist(response.data);
    } catch (error) {
      console.error("Error fetching wishlist:", error);
    } finally {
      setLoading(false);
    }
  };

  const addToWishlist = async (productId) => {
    if (!token) return false;
    try {
      await axios.post(
        `${API}/wishlist/add`,
        { product_id: productId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchWishlist();
      return true;
    } catch (error) {
      console.error("Error adding to wishlist:", error);
      return false;
    }
  };

  const removeFromWishlist = async (productId) => {
    if (!token) return false;
    try {
      await axios.delete(`${API}/wishlist/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchWishlist();
      return true;
    } catch (error) {
      console.error("Error removing from wishlist:", error);
      return false;
    }
  };

  const isInWishlist = (productId) => {
    return wishlist.items.some(item => item.id === productId);
  };

  const toggleWishlist = async (productId) => {
    if (isInWishlist(productId)) {
      return await removeFromWishlist(productId);
    } else {
      return await addToWishlist(productId);
    }
  };

  return (
    <WishlistContext.Provider value={{
      wishlist,
      loading,
      addToWishlist,
      removeFromWishlist,
      isInWishlist,
      toggleWishlist,
      fetchWishlist
    }}>
      {children}
    </WishlistContext.Provider>
  );
};

// Protected Route wrapper
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDF8F3]">
        <div className="animate-pulse text-[#2D4A3E] text-lg">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return (
      <>
        <div className="min-h-screen flex flex-col items-center justify-center bg-[#FDF8F3] p-8">
          <h2 className="text-3xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">Sign in to continue</h2>
          <p className="text-[#5C6D5E] mb-6 text-center max-w-md">
            Create a free account to access this feature and get 15% off your first order.
          </p>
          <button
            onClick={() => setShowAuth(true)}
            className="bg-[#2D4A3E] text-white px-8 py-4 rounded-full font-medium hover:bg-[#1F342B] transition-all"
            data-testid="signin-cta-btn"
          >
            Sign In or Create Account
          </button>
        </div>
        <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      </>
    );
  }
  
  if (adminOnly && !user.is_admin) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

// Layout with Navbar
const AppLayout = ({ children }) => {
  const [showAuth, setShowAuth] = useState(false);
  const { cartOpen, setCartOpen, cart } = useCart();
  
  return (
    <div className="min-h-screen bg-[#FDF8F3] flex flex-col">
      <Navbar onAuthClick={() => setShowAuth(true)} />
      <main className="flex-1">{children}</main>
      <Footer />
      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      <CartDrawer isOpen={cartOpen} onClose={() => setCartOpen(false)} />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <WishlistProvider>
          <BrowserRouter>
            <Toaster 
              position="top-right"
              toastOptions={{
                style: {
                  background: '#FDF8F3',
                  color: '#2D4A3E',
                  border: '1px solid #E8DFD5',
                  fontFamily: 'Nunito, sans-serif'
                }
              }}
            />
            <Routes>
              <Route path="/" element={<AppLayout><HomePage /></AppLayout>} />
              <Route path="/products" element={<AppLayout><ProductsPage /></AppLayout>} />
              <Route path="/products/:slug" element={<AppLayout><ProductDetailPage /></AppLayout>} />
              <Route path="/cart" element={<AppLayout><CartPage /></AppLayout>} />
              <Route path="/wishlist" element={
                <AppLayout>
                  <ProtectedRoute><WishlistPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/order-confirmation" element={<AppLayout><CheckoutSuccessPage /></AppLayout>} />
              <Route path="/account" element={
                <AppLayout>
                  <ProtectedRoute><AccountPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/referral" element={
                <AppLayout>
                  <ReferralPage />
                </AppLayout>
              } />
              <Route path="/support" element={
                <AppLayout>
                  <SupportPage />
                </AppLayout>
              } />
              <Route path="/admin" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/promotions" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminPromotionsPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/products" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminProductsPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/orders" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminOrdersPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/analytics" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminAnalyticsPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/emails" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminEmailAutomationPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/segments" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminCustomerSegmentsPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/agents" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AgentsPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="/admin/sourcing" element={
                <AppLayout>
                  <ProtectedRoute adminOnly><AdminSourcingPage /></ProtectedRoute>
                </AppLayout>
              } />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </WishlistProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
