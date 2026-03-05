import React, { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import LandingPage from "./pages/LandingPage";
import ResearchPage from "./pages/ResearchPage";
import PipelinePage from "./pages/PipelinePage";
import HistoryPage from "./pages/HistoryPage";
import AuthModal from "./components/AuthModal";
import Navbar from "./components/Navbar";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("petpulse_token"));

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
      localStorage.removeItem("petpulse_token");
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem("petpulse_token", newToken);
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name });
    const { token: newToken, user: userData, message } = response.data;
    localStorage.setItem("petpulse_token", newToken);
    setToken(newToken);
    setUser(userData);
    return { user: userData, message };
  };

  const logout = () => {
    localStorage.removeItem("petpulse_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, API }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFCF8]">
        <div className="animate-pulse-soft text-[#2F3E32] text-lg">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return (
      <>
        <div className="min-h-screen flex flex-col items-center justify-center bg-[#FDFCF8] p-8">
          <h2 className="text-3xl font-bold text-[#2F3E32] mb-4 font-['Fraunces']">Sign in to continue</h2>
          <p className="text-[#57534E] mb-6 text-center max-w-md">
            Create a free account to save your product research, track your pipeline, and unlock exclusive features.
          </p>
          <button
            onClick={() => setShowAuth(true)}
            className="bg-[#2F3E32] text-white px-8 py-4 rounded-full font-medium hover:bg-[#253229] transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            data-testid="signin-cta-btn"
          >
            Get Started Free
          </button>
        </div>
        <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
      </>
    );
  }
  
  return children;
};

// Layout with Navbar
const AppLayout = ({ children, showNavbar = true }) => {
  const [showAuth, setShowAuth] = useState(false);
  
  return (
    <div className="min-h-screen bg-[#FDFCF8]">
      {showNavbar && <Navbar onAuthClick={() => setShowAuth(true)} />}
      {children}
      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: '#F2F0E9',
              color: '#2F3E32',
              border: '1px solid #E8E6DE',
              fontFamily: 'Manrope, sans-serif'
            }
          }}
        />
        <Routes>
          <Route path="/" element={
            <AppLayout>
              <LandingPage />
            </AppLayout>
          } />
          <Route path="/research" element={
            <AppLayout>
              <ResearchPage />
            </AppLayout>
          } />
          <Route path="/pipeline" element={
            <AppLayout>
              <ProtectedRoute>
                <PipelinePage />
              </ProtectedRoute>
            </AppLayout>
          } />
          <Route path="/history" element={
            <AppLayout>
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            </AppLayout>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
