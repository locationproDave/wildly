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
  Bot,
  ChevronDown,
  Dog,
  Cat,
  Bird,
  Fish,
  Squirrel,
  Sparkles
} from "lucide-react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "./ui/hover-card";
import { Avatar, AvatarFallback } from "./ui/avatar";
import RealTimeNotifications from "./RealTimeNotifications";

const Navbar = ({ onAuthClick }) => {
  const { user, logout } = useAuth();
  const { cart, setCartOpen } = useCart();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const petCategories = [
    { path: "/products?pet_type=dog", label: "Dogs", icon: Dog },
    { path: "/products?pet_type=cat", label: "Cats", icon: Cat },
    { path: "/products?pet_type=bird", label: "Birds", icon: Bird },
    { path: "/products?pet_type=fish", label: "Fish", icon: Fish },
    { path: "/products?pet_type=rabbit", label: "Rabbits", icon: Squirrel },
    { path: "/products?pet_type=small_pet", label: "Small Pets", icon: Sparkles },
  ];

  const productCategories = [
    { path: "/products?category=supplements", label: "Supplements" },
    { path: "/products?category=calming", label: "Calming" },
    { path: "/products?category=beds", label: "Beds & Blankets" },
    { path: "/products?category=grooming", label: "Grooming" },
    { path: "/products?category=toys", label: "Toys" },
    { path: "/products?category=food", label: "Food & Treats" },
  ];

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-[#E8DFD5]/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center" data-testid="nav-logo">
            <span className="text-[#2D4A3E] text-2xl sm:text-3xl font-['Dancing_Script'] font-bold tracking-wide">Wildly Ones</span>
          </Link>

          {/* Desktop Navigation - Larger font, dark green, hover dropdowns */}
          <div className="hidden md:flex items-center gap-6">
            {/* Shop All with hover dropdown */}
            <HoverCard openDelay={0} closeDelay={100}>
              <HoverCardTrigger asChild>
                <Link
                  to="/products"
                  className="flex items-center gap-1 text-base font-semibold text-[#2D4A3E] hover:text-[#1F342B] transition-colors"
                  data-testid="nav-link-shop"
                >
                  Shop All
                  <ChevronDown className="w-4 h-4" />
                </Link>
              </HoverCardTrigger>
              <HoverCardContent className="w-64 p-2" align="start">
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-[#5C6D5E] px-2 py-1">By Category</p>
                  {productCategories.map((cat) => (
                    <Link
                      key={cat.path}
                      to={cat.path}
                      className="flex items-center px-3 py-2 text-sm text-[#2D4A3E] hover:bg-[#E8DFD5] rounded-lg transition-colors"
                    >
                      {cat.label}
                    </Link>
                  ))}
                </div>
              </HoverCardContent>
            </HoverCard>

            {/* Pets dropdown */}
            <HoverCard openDelay={0} closeDelay={100}>
              <HoverCardTrigger asChild>
                <span className="flex items-center gap-1 text-base font-semibold text-[#2D4A3E] hover:text-[#1F342B] transition-colors cursor-pointer">
                  By Pet
                  <ChevronDown className="w-4 h-4" />
                </span>
              </HoverCardTrigger>
              <HoverCardContent className="w-56 p-2" align="start">
                <div className="space-y-1">
                  {petCategories.map((pet) => {
                    const Icon = pet.icon;
                    return (
                      <Link
                        key={pet.path}
                        to={pet.path}
                        className="flex items-center gap-3 px-3 py-2 text-sm text-[#2D4A3E] hover:bg-[#E8DFD5] rounded-lg transition-colors"
                      >
                        <Icon className="w-4 h-4 text-[#6B8F71]" />
                        {pet.label}
                      </Link>
                    );
                  })}
                </div>
              </HoverCardContent>
            </HoverCard>

            {/* Direct links - larger font, dark green */}
            <Link
              to="/products?pet_type=dog"
              className="text-base font-semibold text-[#2D4A3E] hover:text-[#1F342B] transition-colors"
              data-testid="nav-link-dogs"
            >
              Dogs
            </Link>
            <Link
              to="/referral"
              className="text-base font-semibold text-[#D4A574] hover:text-[#B8956A] transition-colors"
              data-testid="nav-link-referral"
            >
              Refer & Earn
            </Link>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Real-time Notifications (Admin only) */}
            {user?.is_admin && <RealTimeNotifications />}
            
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

      {/* Mobile Menu - Tighter spacing */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-[#E8DFD5] animate-fade-in">
          <div className="px-3 py-2 space-y-1">
            <Link
              to="/products"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#2D4A3E] font-semibold hover:bg-[#E8DFD5]"
            >
              Shop All
            </Link>
            <div className="border-t border-[#E8DFD5] my-1"></div>
            <p className="text-xs font-semibold text-[#5C6D5E] px-3 py-1">Shop by Pet</p>
            {petCategories.map((pet) => {
              const Icon = pet.icon;
              return (
                <Link
                  key={pet.path}
                  to={pet.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-[#2D4A3E] hover:bg-[#E8DFD5]"
                >
                  <Icon className="w-4 h-4 text-[#6B8F71]" />
                  {pet.label}
                </Link>
              );
            })}
            <div className="border-t border-[#E8DFD5] my-1"></div>
            <Link
              to="/referral"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#D4A574] font-semibold hover:bg-[#E8DFD5]"
            >
              Refer & Earn $10
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
