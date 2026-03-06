import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth, useCart, useWishlist } from "../App";
import { 
  ShoppingBag, 
  Menu, 
  X,
  User,
  LogOut,
  Package,
  Settings,
  Bot,
  Dog,
  Cat,
  Bird,
  Fish,
  Rabbit,
  Rat,
  Egg,
  Heart
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
  const { wishlist } = useWishlist();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const petCategories = [
    { path: "/products?pet_type=dog", label: "Dogs", icon: Dog },
    { path: "/products?pet_type=cat", label: "Cats", icon: Cat },
    { path: "/products?pet_type=bird", label: "Birds", icon: Bird },
    { path: "/products?pet_type=fish", label: "Fish", icon: Fish },
    { path: "/products?pet_type=rabbit", label: "Rabbits", icon: Rabbit },
    { path: "/products?pet_type=small_pet", label: "Small Pets", icon: Rat },
    { path: "/products?pet_type=chicken", label: "Chickens", icon: Egg },
  ];

  // Pet-specific product categories
  const petProductCategories = {
    dog: [
      { path: "supplements", label: "Supplements" },
      { path: "food", label: "Food & Treats" },
      { path: "grooming", label: "Grooming" },
      { path: "toys", label: "Toys" },
      { path: "home_goods", label: "Beds & Crates" },
    ],
    cat: [
      { path: "supplements", label: "Supplements" },
      { path: "food", label: "Food & Treats" },
      { path: "grooming", label: "Grooming" },
      { path: "toys", label: "Toys & Scratchers" },
      { path: "home_goods", label: "Beds & Litter" },
    ],
    bird: [
      { path: "supplements", label: "Vitamins" },
      { path: "food", label: "Seeds & Treats" },
      { path: "toys", label: "Perches & Toys" },
      { path: "home_goods", label: "Cages & Accessories" },
    ],
    fish: [
      { path: "supplements", label: "Water Care" },
      { path: "food", label: "Fish Food" },
      { path: "home_goods", label: "Tank & Decor" },
      { path: "toys", label: "Plants & Hideouts" },
    ],
    rabbit: [
      { path: "supplements", label: "Supplements" },
      { path: "food", label: "Hay & Treats" },
      { path: "grooming", label: "Grooming" },
      { path: "toys", label: "Chews & Toys" },
      { path: "home_goods", label: "Hutches & Bedding" },
    ],
    small_pet: [
      { path: "supplements", label: "Vitamins" },
      { path: "food", label: "Food & Treats" },
      { path: "home_goods", label: "Cages & Bedding" },
      { path: "toys", label: "Wheels & Toys" },
    ],
    chicken: [
      { path: "supplements", label: "Supplements" },
      { path: "food", label: "Feed & Treats" },
      { path: "home_goods", label: "Coops & Nesting" },
      { path: "toys", label: "Enrichment" },
    ],
  };

  const getProductCategories = (petType) => {
    const type = petType.split('=')[1];
    return petProductCategories[type] || petProductCategories.dog;
  };

  const getInitials = (name) => {
    return name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U";
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#F5F0E8] border-b border-[#E8DFD5]/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center flex-shrink-0" data-testid="nav-logo">
            <span 
              className="text-[#2D4A3E] text-[2rem] sm:text-[2.7rem] font-['Dancing_Script'] font-bold tracking-wide"
              style={{ WebkitTextStroke: '1.2px #2D4A3E' }}
            >
              Wildly Ones
            </span>
          </Link>

          {/* Desktop Navigation - Pet types with hover dropdowns */}
          <div className="hidden lg:flex items-center gap-5">
            {/* Each pet type as main nav item with hover dropdown for categories */}
            {petCategories.map((pet) => {
              const Icon = pet.icon;
              return (
                <HoverCard key={pet.path} openDelay={0} closeDelay={150}>
                  <HoverCardTrigger asChild>
                    <Link
                      to={pet.path}
                      className="flex items-center gap-1.5 text-[15px] font-semibold text-[#2D4A3E] hover:text-[#6B8F71] transition-colors whitespace-nowrap"
                      data-testid={`nav-link-${pet.label.toLowerCase()}`}
                    >
                      <Icon className="w-4 h-4" />
                      {pet.label}
                    </Link>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-40 p-1.5" align="center" sideOffset={8}>
                    <div className="space-y-0.5">
                      {getProductCategories(pet.path).map((cat) => (
                        <Link
                          key={cat.path}
                          to={`${pet.path}&category=${cat.path}`}
                          className="flex items-center justify-center px-2 py-1.5 text-sm text-[#2D4A3E] hover:bg-[#E8DFD5] rounded-md transition-colors"
                        >
                          {cat.label}
                        </Link>
                      ))}
                    </div>
                  </HoverCardContent>
                </HoverCard>
              );
            })}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-3 sm:gap-4">
            {/* Real-time Notifications (Admin only) */}
            {user?.is_admin && <RealTimeNotifications />}
            
            {/* Wishlist */}
            {user && (
              <Link
                to="/wishlist"
                className="relative p-2 hover:bg-white/20 rounded-full transition-colors"
                data-testid="wishlist-nav-btn"
              >
                <Heart className="w-5 h-5 text-[#2D4A3E]" />
                {wishlist.count > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#D66D5A] text-white text-xs rounded-full flex items-center justify-center">
                    {wishlist.count}
                  </span>
                )}
              </Link>
            )}
            
            {/* Cart */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2 hover:bg-white/20 rounded-full transition-colors"
              data-testid="cart-btn"
            >
              <ShoppingBag className="w-5 h-5 text-[#2D4A3E]" />
              {cart.item_count > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#2D4A3E] text-white text-xs rounded-full flex items-center justify-center">
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
                Sign Up / Sign In
              </Button>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-[#2D4A3E]"
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
