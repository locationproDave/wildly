import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import AdminSidebar from "../components/admin/AdminSidebar";
import { 
  Package, 
  DollarSign, 
  Users, 
  ShoppingCart,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  Clock,
  Truck,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  MoreHorizontal,
  Eye,
  RefreshCw
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

  useEffect(() => {
    fetchStats();
    fetchOrders();
  }, []);

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
      const response = await axios.get(`${BACKEND_URL}/api/admin/orders`, {
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

  const getStatusConfig = (status) => {
    const config = {
      pending: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", icon: Clock },
      processing: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", icon: RefreshCw },
      shipped: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200", icon: Truck },
      delivered: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200", icon: CheckCircle },
      cancelled: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", icon: XCircle }
    };
    return config[status] || config.pending;
  };

  const statCards = [
    { 
      label: "Total Revenue", 
      value: `$${stats?.total_revenue?.toFixed(2) || "0.00"}`,
      change: "+12.5%",
      trend: "up",
      icon: DollarSign,
      color: "from-emerald-500 to-emerald-600"
    },
    { 
      label: "Total Orders", 
      value: stats?.total_orders || 0,
      change: "+8.2%",
      trend: "up",
      icon: ShoppingCart,
      color: "from-blue-500 to-blue-600"
    },
    { 
      label: "Products", 
      value: stats?.total_products || 0,
      change: "+3",
      trend: "up",
      icon: Package,
      color: "from-violet-500 to-violet-600"
    },
    { 
      label: "Customers", 
      value: stats?.total_customers || 0,
      change: "+24",
      trend: "up",
      icon: Users,
      color: "from-amber-500 to-amber-600"
    }
  ];

  const pendingOrders = orders.filter(o => o.status === "pending").length;
  const processingOrders = orders.filter(o => o.status === "processing").length;
  const shippedOrders = orders.filter(o => o.status === "shipped").length;
  const deliveredOrders = orders.filter(o => o.status === "delivered").length;

  return (
    <AdminSidebar>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#2F3E32] font-['Fraunces']">
              Welcome back! 👋
            </h1>
            <p className="text-[#5C6D5E] mt-1">
              Here's what's happening with your store today.
            </p>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => { fetchStats(); fetchOrders(); }}
              className="rounded-lg"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div
                key={index}
                className="bg-white rounded-2xl border border-[#E8E6DE] p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className={`flex items-center gap-1 text-sm ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                    {stat.trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    {stat.change}
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-bold text-[#2F3E32]">{stat.value}</p>
                  <p className="text-sm text-[#5C6D5E]">{stat.label}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Order Status Overview */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
            <Clock className="w-8 h-8 text-amber-600" />
            <div>
              <p className="text-2xl font-bold text-amber-700">{pendingOrders}</p>
              <p className="text-sm text-amber-600">Pending</p>
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-3">
            <RefreshCw className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-2xl font-bold text-blue-700">{processingOrders}</p>
              <p className="text-sm text-blue-600">Processing</p>
            </div>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-center gap-3">
            <Truck className="w-8 h-8 text-purple-600" />
            <div>
              <p className="text-2xl font-bold text-purple-700">{shippedOrders}</p>
              <p className="text-sm text-purple-600">Shipped</p>
            </div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-2xl font-bold text-green-700">{deliveredOrders}</p>
              <p className="text-sm text-green-600">Delivered</p>
            </div>
          </div>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-2xl border border-[#E8E6DE] overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-[#E8E6DE]">
            <div>
              <h2 className="text-lg font-semibold text-[#2F3E32]">Recent Orders</h2>
              <p className="text-sm text-[#5C6D5E]">{orders.length} total orders</p>
            </div>
            <Link to="/admin/orders">
              <Button variant="outline" size="sm" className="rounded-lg">
                View All
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
          
          {loading ? (
            <div className="p-10 text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-[#5C6D5E] mx-auto" />
              <p className="text-[#5C6D5E] mt-2">Loading orders...</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="p-10 text-center">
              <ShoppingCart className="w-12 h-12 text-[#D4D4D4] mx-auto mb-3" />
              <p className="text-[#5C6D5E]">No orders yet</p>
            </div>
          ) : (
            <div className="divide-y divide-[#E8E6DE]">
              {orders.slice(0, 8).map((order) => {
                const statusConfig = getStatusConfig(order.status);
                const StatusIcon = statusConfig.icon;
                
                return (
                  <div 
                    key={order.id}
                    className="flex items-center justify-between p-4 hover:bg-[#FAFAF8] transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg ${statusConfig.bg} ${statusConfig.border} border flex items-center justify-center`}>
                        <StatusIcon className={`w-5 h-5 ${statusConfig.text}`} />
                      </div>
                      <div>
                        <p className="font-medium text-[#2F3E32]">{order.order_number}</p>
                        <p className="text-sm text-[#5C6D5E]">{order.email}</p>
                      </div>
                    </div>
                    
                    <div className="hidden sm:block text-right">
                      <p className="font-medium text-[#2F3E32]">${order.total?.toFixed(2)}</p>
                      <p className="text-sm text-[#5C6D5E]">{order.items?.length} items</p>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Badge className={`${statusConfig.bg} ${statusConfig.text} ${statusConfig.border} border capitalize`}>
                        {order.status}
                      </Badge>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "processing")}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Mark Processing
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "shipped")}>
                            <Truck className="w-4 h-4 mr-2" />
                            Mark Shipped
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "delivered")}>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Mark Delivered
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => updateOrderStatus(order.id, "cancelled")}
                            className="text-red-600"
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Cancel Order
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/admin/products" className="block">
            <div className="bg-white rounded-2xl border border-[#E8E6DE] p-5 hover:shadow-md hover:border-[#2D4A3E] transition-all group">
              <Package className="w-8 h-8 text-[#2D4A3E] mb-3" />
              <h3 className="font-semibold text-[#2F3E32] group-hover:text-[#2D4A3E]">Manage Products</h3>
              <p className="text-sm text-[#5C6D5E] mt-1">Add, edit, or remove products</p>
            </div>
          </Link>
          <Link to="/admin/sourcing" className="block">
            <div className="bg-white rounded-2xl border border-[#E8E6DE] p-5 hover:shadow-md hover:border-[#6B8F71] transition-all group relative">
              <Badge className="absolute top-3 right-3 bg-[#D66D5A] text-white">NEW</Badge>
              <TrendingUp className="w-8 h-8 text-[#6B8F71] mb-3" />
              <h3 className="font-semibold text-[#2F3E32] group-hover:text-[#6B8F71]">Source Products</h3>
              <p className="text-sm text-[#5C6D5E] mt-1">Find products from suppliers</p>
            </div>
          </Link>
          <Link to="/admin/analytics" className="block">
            <div className="bg-white rounded-2xl border border-[#E8E6DE] p-5 hover:shadow-md hover:border-[#7CA5B8] transition-all group">
              <TrendingUp className="w-8 h-8 text-[#7CA5B8] mb-3" />
              <h3 className="font-semibold text-[#2F3E32] group-hover:text-[#7CA5B8]">View Analytics</h3>
              <p className="text-sm text-[#5C6D5E] mt-1">Track sales and performance</p>
            </div>
          </Link>
        </div>
      </div>
    </AdminSidebar>
  );
};

export default AdminDashboard;
