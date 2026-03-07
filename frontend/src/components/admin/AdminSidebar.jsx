import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../App";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  BarChart3,
  Mail,
  Tag,
  Bot,
  Search,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Store,
  Menu,
  X,
  Bell,
  UserCircle,
  Megaphone
} from "lucide-react";
import { Button } from "../ui/button";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Badge } from "../ui/badge";

const AdminSidebar = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigation = [
    {
      name: "Dashboard",
      href: "/admin",
      icon: LayoutDashboard,
      exact: true
    },
    {
      name: "Orders",
      href: "/admin/orders",
      icon: ShoppingCart,
      badge: null
    },
    {
      name: "Products",
      href: "/admin/products",
      icon: Package
    },
    {
      name: "Source Products",
      href: "/admin/sourcing",
      icon: Search,
      badge: "NEW"
    },
    {
      name: "Analytics",
      href: "/admin/analytics",
      icon: BarChart3
    },
    {
      name: "Promotions",
      href: "/admin/promotions",
      icon: Tag
    },
    {
      name: "Email Campaigns",
      href: "/admin/emails",
      icon: Mail
    },
    {
      name: "Customer Segments",
      href: "/admin/segments",
      icon: Users
    },
    {
      name: "AI Agents",
      href: "/admin/agents",
      icon: Bot
    }
  ];

  const isActive = (item) => {
    if (item.exact) {
      return location.pathname === item.href;
    }
    return location.pathname.startsWith(item.href);
  };

  const getInitials = (name) => {
    if (!name) return "A";
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} p-4 border-b border-[#3D5A4E]`}>
        {!collapsed && (
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-white font-['Fraunces']">Wildly Ones</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="text-white/70 hover:text-white hover:bg-white/10 hidden lg:flex"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = isActive(item);
          
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={() => setMobileOpen(false)}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all
                ${active 
                  ? 'bg-white/20 text-white font-medium' 
                  : 'text-white/70 hover:bg-white/10 hover:text-white'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? item.name : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-[#D4A574]' : ''}`} />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && (
                    <Badge className="bg-[#D66D5A] text-white text-[10px] px-1.5 py-0">
                      {item.badge}
                    </Badge>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="p-3 border-t border-[#3D5A4E]">
        {/* Back to Store */}
        <Link
          to="/"
          className={`
            flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/70 
            hover:bg-white/10 hover:text-white transition-all mb-2
            ${collapsed ? 'justify-center' : ''}
          `}
        >
          <Store className="w-5 h-5" />
          {!collapsed && <span>Back to Store</span>}
        </Link>

        {/* User Profile */}
        <div className={`
          flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/5
          ${collapsed ? 'justify-center' : ''}
        `}>
          <Avatar className="h-8 w-8 border border-[#D4A574]">
            <AvatarFallback className="bg-[#D4A574] text-white text-sm">
              {getInitials(user?.name)}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name}</p>
              <p className="text-xs text-white/50 truncate">{user?.email}</p>
            </div>
          )}
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className={`
            flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/70 
            hover:bg-red-500/20 hover:text-red-300 transition-all w-full mt-2
            ${collapsed ? 'justify-center' : ''}
          `}
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FDF8F3]">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-[#2D4A3E] z-40 flex items-center justify-between px-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setMobileOpen(true)}
          className="text-white"
        >
          <Menu className="w-6 h-6" />
        </Button>
        <span className="text-lg font-bold text-white font-['Fraunces']">Admin</span>
        <Link to="/" className="text-white/70 hover:text-white">
          <Store className="w-5 h-5" />
        </Link>
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div className={`
        lg:hidden fixed top-0 left-0 h-full w-72 bg-[#2D4A3E] z-50 
        transform transition-transform duration-300
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex justify-end p-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMobileOpen(false)}
            className="text-white"
          >
            <X className="w-6 h-6" />
          </Button>
        </div>
        <SidebarContent />
      </div>

      {/* Desktop Sidebar */}
      <div className={`
        hidden lg:block fixed top-0 left-0 h-full bg-[#2D4A3E] z-30
        transition-all duration-300
        ${collapsed ? 'w-20' : 'w-64'}
      `}>
        <SidebarContent />
      </div>

      {/* Main Content */}
      <div className={`
        transition-all duration-300
        lg:ml-64 ${collapsed ? 'lg:ml-20' : 'lg:ml-64'}
        pt-16 lg:pt-0
      `}>
        {/* Top Bar */}
        <div className="hidden lg:flex h-16 bg-white border-b border-[#E8E6DE] items-center justify-between px-6 sticky top-0 z-20">
          <div>
            <h1 className="text-lg font-semibold text-[#2F3E32]">
              {navigation.find(n => isActive(n))?.name || 'Dashboard'}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="relative">
              <Bell className="w-5 h-5 text-[#5C6D5E]" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-[#D66D5A] rounded-full" />
            </Button>
            <div className="h-8 w-px bg-[#E8E6DE]" />
            <div className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-[#2D4A3E] text-white text-sm">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-[#2F3E32]">{user?.name}</span>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="p-4 lg:p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default AdminSidebar;
