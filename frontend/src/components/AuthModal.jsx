import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { toast } from "sonner";
import { 
  X, 
  Mail, 
  Lock, 
  User,
  Gift,
  Loader2
} from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";

const AuthModal = ({ isOpen, onClose }) => {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const userData = await login(formData.email, formData.password);
        toast.success("Welcome back!");
        onClose();
        setFormData({ email: "", password: "", name: "" });
        // Redirect admin users to admin dashboard
        if (userData?.is_admin) {
          navigate("/admin");
        }
      } else {
        const result = await register(formData.email, formData.password, formData.name);
        toast.success(result.message || "Account created!");
        onClose();
        setFormData({ email: "", password: "", name: "" });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setFormData({ email: "", password: "", name: "" });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-[#FDF8F3] border-[#E8DFD5]">
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <span className="text-4xl">🐾</span>
          </div>
          <DialogTitle className="text-center text-2xl font-bold text-[#2D4A3E] font-['Fraunces']">
            {isLogin ? "Welcome Back" : "Join Wildly Ones"}
          </DialogTitle>
          <DialogDescription className="text-center text-sm text-[#5C6D5E]">
            {isLogin 
              ? "Sign in to view your orders and saved items."
              : "Create your account to get started."
            }
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="name" className="text-[#2D4A3E]">Name</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5C6D5E]" />
                <Input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="Your name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="pl-10 rounded-xl border-[#E8DFD5] focus:ring-2 focus:ring-[#2D4A3E]/20 focus:border-[#2D4A3E]"
                  required={!isLogin}
                  data-testid="auth-name-input"
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email" className="text-[#2D4A3E]">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5C6D5E]" />
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleInputChange}
                className="pl-10 rounded-xl border-[#E8DFD5] focus:ring-2 focus:ring-[#2D4A3E]/20 focus:border-[#2D4A3E]"
                required
                data-testid="auth-email-input"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-[#2D4A3E]">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5C6D5E]" />
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange}
                className="pl-10 rounded-xl border-[#E8DFD5] focus:ring-2 focus:ring-[#2D4A3E]/20 focus:border-[#2D4A3E]"
                required
                minLength={6}
                data-testid="auth-password-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#2D4A3E] hover:bg-[#1F342B] text-white rounded-xl py-6 font-medium"
            data-testid="auth-submit-btn"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              isLogin ? "Sign In" : "Create Account"
            )}
          </Button>
        </form>

        <div className="text-center mt-4">
          <button
            type="button"
            onClick={switchMode}
            className="text-sm text-[#5C6D5E] hover:text-[#2D4A3E] transition-colors"
            data-testid="auth-switch-mode-btn"
          >
            {isLogin ? (
              <>Don't have an account? <span className="font-semibold text-[#D4A574]">Sign up</span></>
            ) : (
              <>Already have an account? <span className="font-semibold text-[#D4A574]">Sign in</span></>
            )}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
