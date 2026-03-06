import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { 
  Package, 
  DollarSign, 
  Users, 
  ShoppingBag,
  Bot,
  ChevronRight,
  Clock,
  Truck,
  CheckCircle,
  Tag,
  PackagePlus,
  ClipboardList,
  BarChart3,
  Mail,
  UserCircle
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminDashboard = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    fetchStats();
    fetchOrders();
  }, [statusFilter]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchOrders = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const response = await axios.get(`${BACKEND_URL}/api/admin/orders${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(response.data);
    } catch (error) {
      console.error("Error fetching orders:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.patch(
        `${BACKEND_URL}/api/admin/orders/${orderId}?status=${status}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchOrders();
      fetchStats();
    } catch (error) {
      console.error("Error updating order:", error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-yellow-100 text-yellow-800",
      processing: "bg-blue-100 text-blue-800",
      shipped: "bg-purple-100 text-purple-800",
      delivered: "bg-green-100 text-green-800",
      cancelled: "bg-red-100 text-red-800"
    };
    return styles[status] || "bg-gray-100 text-gray-800";
  };

  const statCards = [
    { icon: <DollarSign className="w-6 h-6" />, label: "Total Revenue", value: `$${stats?.total_revenue?.toFixed(2) || "0.00"}`, color: "bg-[#6B8F71]" },
    { icon: <Package className="w-6 h-6" />, label: "Total Orders", value: stats?.total_orders || 0, color: "bg-[#2D4A3E]" },
    { icon: <ShoppingBag className="w-6 h-6" />, label: "Products", value: stats?.total_products || 0, color: "bg-[#D4A574]" },
    { icon: <Users className="w-6 h-6" />, label: "Customers", value: stats?.total_customers || 0, color: "bg-[#7CA5B8]" }
  ];

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        {/* Header - Mobile Optimized */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 sm:mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-[#2D4A3E] font-['Fraunces']">
              Admin Dashboard
            </h1>
            <p className="text-sm sm:text-base text-[#5C6D5E]">Manage your store</p>
          </div>
          {/* Navigation - Scrollable on mobile */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 -mx-3 px-3 sm:mx-0 sm:px-0 sm:gap-3 sm:flex-wrap scrollbar-hide">
            <Link to="/admin/analytics">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="analytics-btn">
                <BarChart3 className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Analytics</span>
              </Button>
            </Link>
            <Link to="/admin/segments">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="segments-btn">
                <UserCircle className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Segments</span>
              </Button>
            </Link>
            <Link to="/admin/emails">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="emails-btn">
                <Mail className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Emails</span>
              </Button>
            </Link>
            <Link to="/admin/orders">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="orders-btn">
                <ClipboardList className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Orders</span>
              </Button>
            </Link>
            <Link to="/admin/products">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="products-btn">
                <PackagePlus className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Products</span>
              </Button>
            </Link>
            <Link to="/admin/promotions">
              <Button variant="outline" size="sm" className="rounded-full whitespace-nowrap" data-testid="promotions-btn">
                <Tag className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Promotions</span>
              </Button>
            </Link>
            <Link to="/admin/agents">
              <Button size="sm" className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full whitespace-nowrap" data-testid="agents-btn">
                <Bot className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">AI Agents</span>
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats - Responsive Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          {statCards.map((stat, index) => (
            <div key={index} className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm" data-testid={`stat-${index}`}>
              <div className="flex items-center gap-3 sm:gap-4">
                <div className={`w-10 h-10 sm:w-12 sm:h-12 ${stat.color} rounded-lg sm:rounded-xl flex items-center justify-center text-white flex-shrink-0`}>
                  {stat.icon}
                </div>
                <div className="min-w-0">
                  <p className="text-lg sm:text-2xl font-bold text-[#2D4A3E] truncate">{stat.value}</p>
                  <p className="text-xs sm:text-sm text-[#5C6D5E]">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Pipeline - Scrollable on mobile */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4 mb-6 sm:mb-8">
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all ${statusFilter === "" ? "ring-2 ring-[#2D4A3E]" : ""}`}
            onClick={() => setStatusFilter("")}
          >
            <div className="flex items-center gap-3">
              <Package className="w-5 h-5 text-[#5C6D5E]" />
              <span className="font-medium text-[#2D4A3E]">All Orders</span>
              <span className="ml-auto bg-[#E8DFD5] px-2 py-1 rounded-full text-sm">{stats?.total_orders || 0}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all ${statusFilter === "pending" ? "ring-2 ring-yellow-500" : ""}`}
            onClick={() => setStatusFilter("pending")}
          >
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-yellow-600" />
              <span className="font-medium text-[#2D4A3E]">Pending</span>
              <span className="ml-auto bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-sm">{stats?.pending_orders || 0}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all ${statusFilter === "processing" ? "ring-2 ring-blue-500" : ""}`}
            onClick={() => setStatusFilter("processing")}
          >
            <div className="flex items-center gap-3">
              <Truck className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-[#2D4A3E]">Processing</span>
              <span className="ml-auto bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">{stats?.processing_orders || 0}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all ${statusFilter === "shipped" ? "ring-2 ring-purple-500" : ""}`}
            onClick={() => setStatusFilter("shipped")}
          >
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-purple-600" />
              <span className="font-medium text-[#2D4A3E]">Shipped</span>
              <span className="ml-auto bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-sm">{stats?.shipped_orders || 0}</span>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#E8DFD5]">
            <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">
              Recent Orders
            </h2>
          </div>
          
          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : orders.length === 0 ? (
            <div className="p-12 text-center">
              <Package className="w-12 h-12 text-[#5C6D5E] mx-auto mb-4" />
              <p className="text-[#5C6D5E]">No orders found</p>
            </div>
          ) : (
            <div className="divide-y divide-[#E8DFD5]">
              {orders.map((order) => (
                <div key={order.id} className="p-4 hover:bg-[#FDF8F3] transition-colors" data-testid={`order-row-${order.id}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="font-semibold text-[#2D4A3E]">{order.order_number}</p>
                        <p className="text-sm text-[#5C6D5E]">{order.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="font-semibold text-[#2D4A3E]">${order.total.toFixed(2)}</p>
                        <p className="text-sm text-[#5C6D5E]">
                          {order.items.length} item{order.items.length > 1 ? "s" : ""}
                        </p>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm" className="rounded-full">
                            <Badge className={getStatusBadge(order.status)}>
                              {order.status}
                            </Badge>
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "pending")}>
                            Mark as Pending
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "processing")}>
                            Mark as Processing
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "shipped")}>
                            Mark as Shipped
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "delivered")}>
                            Mark as Delivered
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "cancelled")}>
                            Cancel Order
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
