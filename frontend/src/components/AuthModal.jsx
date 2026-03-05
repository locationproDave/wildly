import React, { useState } from "react";
import { useAuth } from "../App";
import { toast } from "sonner";
import { 
  X, 
  Dog, 
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
} from "./ui/dialog";

const AuthModal = ({ isOpen, onClose }) => {
  const { login, register } = useAuth();
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
        await login(formData.email, formData.password);
        toast.success("Welcome back!");
      } else {
        const result = await register(formData.email, formData.password, formData.name);
        toast.success(result.message || "Account created!");
      }
      onClose();
      setFormData({ email: "", password: "", name: "" });
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
      <DialogContent className="sm:max-w-md bg-[#FDFCF8] border-stone-100">
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-[#2F3E32] rounded-xl flex items-center justify-center">
              <Dog className="w-7 h-7 text-white" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl font-bold text-[#2F3E32] font-['Fraunces']">
            {isLogin ? "Welcome Back" : "Create Account"}
          </DialogTitle>
          {!isLogin && (
            <p className="text-center text-sm text-[#57534E] mt-2">
              <Gift className="inline w-4 h-4 mr-1 text-[#D4A373]" />
              Get 15% off your first month when you sign up!
            </p>
          )}
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="name" className="text-[#2F3E32]">Name</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
                <Input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="Your name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="pl-10 rounded-xl border-stone-200 focus:ring-2 focus:ring-[#2F3E32]/20 focus:border-[#2F3E32]"
                  required={!isLogin}
                  data-testid="auth-name-input"
                />
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="email" className="text-[#2F3E32]">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleInputChange}
                className="pl-10 rounded-xl border-stone-200 focus:ring-2 focus:ring-[#2F3E32]/20 focus:border-[#2F3E32]"
                required
                data-testid="auth-email-input"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-[#2F3E32]">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#A8A29E]" />
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleInputChange}
                className="pl-10 rounded-xl border-stone-200 focus:ring-2 focus:ring-[#2F3E32]/20 focus:border-[#2F3E32]"
                required
                minLength={6}
                data-testid="auth-password-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#2F3E32] hover:bg-[#253229] text-white rounded-xl py-6 font-medium"
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
            className="text-sm text-[#57534E] hover:text-[#2F3E32] transition-colors"
            data-testid="auth-switch-mode-btn"
          >
            {isLogin ? (
              <>Don't have an account? <span className="font-semibold text-[#D4A373]">Sign up</span></>
            ) : (
              <>Already have an account? <span className="font-semibold text-[#D4A373]">Sign in</span></>
            )}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;
