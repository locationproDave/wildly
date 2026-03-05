import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth, useCart } from "../App";
import { 
  ShoppingBag, 
  Menu, 
  X,
  User,
  LogOut,
  Package,
  Settings,
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
  const { cart, setCartOpen } = useCart();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { path: "/products", label: "Shop All" },
    { path: "/products?pet_type=dog", label: "Dogs" },
    { path: "/products?pet_type=cat", label: "Cats" },
    { path: "/products?pet_type=bird", label: "Birds" },
    { path: "/products?pet_type=fish", label: "Fish" },
    { path: "/products?pet_type=rabbit", label: "Rabbits" },
    { path: "/products?pet_type=small_pet", label: "Small Pets" },
  ];

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-[#E8DFD5]/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
            <span className="text-2xl">🐾</span>
            <span className="font-bold text-[#2D4A3E] text-xl font-['Fraunces']">CalmTails</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-medium transition-colors ${
                  location.pathname === link.path.split("?")[0]
                    ? 'text-[#2D4A3E]' 
                    : 'text-[#5C6D5E] hover:text-[#2D4A3E]'
                }`}
                data-testid={`nav-link-${link.label.toLowerCase()}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Cart */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2 hover:bg-[#E8DFD5] rounded-full transition-colors"
              data-testid="cart-btn"
            >
              <ShoppingBag className="w-5 h-5 text-[#2D4A3E]" />
              {cart.item_count > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#D4A574] text-white text-xs rounded-full flex items-center justify-center">
                  {cart.item_count}
                </span>
              )}
            </button>

            {/* User Menu */}
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className="relative h-10 w-10 rounded-full"
                    data-testid="user-menu-trigger"
                  >
                    <Avatar className="h-10 w-10 border-2 border-[#D4A574]">
                      <AvatarFallback className="bg-[#2D4A3E] text-white">
                        {getInitials(user.name)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-3 py-2">
                    <p className="text-sm font-medium text-[#2D4A3E]">{user.name}</p>
                    <p className="text-xs text-[#5C6D5E]">{user.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/account" className="cursor-pointer">
                      <User className="w-4 h-4 mr-2" />
                      My Account
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/account" className="cursor-pointer">
                      <Package className="w-4 h-4 mr-2" />
                      Orders
                    </Link>
                  </DropdownMenuItem>
                  {user.is_admin && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem asChild>
                        <Link to="/admin" className="cursor-pointer">
                          <Settings className="w-4 h-4 mr-2" />
                          Admin Dashboard
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link to="/admin/agents" className="cursor-pointer">
                          <Bot className="w-4 h-4 mr-2" />
                          AI Agents
                        </Link>
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={logout}
                    className="text-[#C45C4A] cursor-pointer"
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
                className="bg-[#2D4A3E] hover:bg-[#1F342B] text-white rounded-full px-6"
                data-testid="nav-signin-btn"
              >
                Sign In
              </Button>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-[#2D4A3E]"
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-[#E8DFD5] animate-fade-in">
          <div className="px-4 py-4 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                  location.pathname === link.path.split("?")[0]
                    ? 'bg-[#2D4A3E]/10 text-[#2D4A3E]' 
                    : 'text-[#5C6D5E] hover:bg-[#E8DFD5]'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
