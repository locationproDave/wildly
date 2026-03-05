import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { 
  Dog, 
  Search, 
  Package, 
  History, 
  Menu, 
  X,
  LogOut,
  User,
  Gift,
  Bot
} from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback } from "./ui/avatar";

const Navbar = ({ onAuthClick }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { path: "/research", label: "Research", icon: <Search className="w-4 h-4" /> },
    { path: "/agents", label: "Agents", icon: <Bot className="w-4 h-4" /> },
    { path: "/pipeline", label: "Pipeline", icon: <Package className="w-4 h-4" />, protected: true },
    { path: "/history", label: "History", icon: <History className="w-4 h-4" />, protected: true },
  ];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
            <div className="w-8 h-8 bg-[#2F3E32] rounded-lg flex items-center justify-center">
              <Dog className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-[#2F3E32] text-lg font-['Fraunces']">PetPulse</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => {
              if (link.protected && !user) return null;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                    location.pathname === link.path 
                      ? 'text-[#2F3E32]' 
                      : 'text-[#57534E] hover:text-[#2F3E32]'
                  }`}
                  data-testid={`nav-link-${link.label.toLowerCase()}`}
                >
                  {link.icon}
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className="relative h-10 w-10 rounded-full"
                    data-testid="user-menu-trigger"
                  >
                    <Avatar className="h-10 w-10 border-2 border-[#D4A373]">
                      <AvatarFallback className="bg-[#2F3E32] text-white">
                        {getInitials(user.name)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-3 py-2">
                    <p className="text-sm font-medium text-[#2F3E32]">{user.name}</p>
                    <p className="text-xs text-[#57534E]">{user.email}</p>
                  </div>
                  {user.discount_code && (
                    <>
                      <DropdownMenuSeparator />
                      <div className="px-3 py-2">
                        <p className="text-xs text-[#57534E] flex items-center gap-1">
                          <Gift className="w-3 h-3 text-[#D4A373]" />
                          Your discount code:
                        </p>
                        <p className="text-sm font-mono font-semibold text-[#768A75]">
                          {user.discount_code}
                        </p>
                      </div>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={handleLogout}
                    className="text-[#D66D5A] cursor-pointer"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button
                onClick={onAuthClick}
                className="bg-[#2F3E32] hover:bg-[#253229] text-white rounded-full px-6"
                data-testid="nav-signin-btn"
              >
                Sign In
              </Button>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-[#2F3E32]"
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-stone-100 animate-fade-in">
          <div className="px-4 py-4 space-y-2">
            {navLinks.map((link) => {
              if (link.protected && !user) return null;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                    location.pathname === link.path 
                      ? 'bg-[#2F3E32]/10 text-[#2F3E32]' 
                      : 'text-[#57534E] hover:bg-[#F2F0E9]'
                  }`}
                  data-testid={`mobile-nav-${link.label.toLowerCase()}`}
                >
                  {link.icon}
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
