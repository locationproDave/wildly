import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import AdminSidebar from "../components/admin/AdminSidebar";
import { 
  ChevronLeft,
  DollarSign,
  ShoppingBag,
  Users,
  TrendingUp,
  Package,
  BarChart3,
  PieChart,
  Calendar,
  ArrowUp,
  ArrowDown
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminAnalyticsPage = () => {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("30");

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/admin/analytics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Simple chart component for sales trend
  const SalesChart = ({ data }) => {
    const maxRevenue = Math.max(...data.map(d => d.revenue), 1);
    const filteredData = data.slice(-parseInt(timeRange));
    
    return (
      <div className="relative h-48">
        <div className="absolute inset-0 flex items-end gap-1">
          {filteredData.map((day, idx) => (
            <div 
              key={day.date}
              className="flex-1 flex flex-col items-center group"
            >
              <div 
                className="w-full bg-[#6B8F71] hover:bg-[#2D4A3E] transition-colors rounded-t cursor-pointer relative"
                style={{ height: `${Math.max((day.revenue / maxRevenue) * 100, 2)}%` }}
              >
                <div className="absolute -top-16 left-1/2 -translate-x-1/2 bg-[#2D4A3E] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {formatDate(day.date)}<br/>
                  {formatCurrency(day.revenue)}<br/>
                  {day.orders} orders
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Category breakdown chart
  const CategoryChart = ({ data }) => {
    const total = data.reduce((sum, d) => sum + d.revenue, 0);
    const colors = [
      "bg-[#2D4A3E]", "bg-[#6B8F71]", "bg-[#D4A574]", 
      "bg-[#7CA5B8]", "bg-[#E8DFD5]", "bg-[#A3C4BC]",
      "bg-[#8B7355]", "bg-[#B8860B]"
    ];
    
    return (
      <div className="space-y-3">
        {data.slice(0, 6).map((cat, idx) => (
          <div key={cat.category} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="capitalize text-[#2D4A3E]">{cat.category}</span>
              <span className="text-[#5C6D5E]">{formatCurrency(cat.revenue)} ({((cat.revenue / total) * 100).toFixed(1)}%)</span>
            </div>
            <div className="h-2 bg-[#E8DFD5] rounded-full overflow-hidden">
              <div 
                className={`h-full ${colors[idx % colors.length]} rounded-full transition-all`}
                style={{ width: `${(cat.revenue / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Pet type breakdown
  const PetTypeChart = ({ data }) => {
    const total = data.reduce((sum, d) => sum + d.revenue, 0);
    const petColors = {
      dog: "bg-amber-500",
      cat: "bg-purple-500",
      bird: "bg-sky-500",
      fish: "bg-blue-500",
      rabbit: "bg-pink-500",
      reptile: "bg-green-600",
      small_pet: "bg-orange-500",
      both: "bg-indigo-500"
    };
    
    return (
      <div className="grid grid-cols-2 gap-3">
        {data.map((pt) => (
          <div key={pt.pet_type} className="bg-[#FDF8F3] rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-3 h-3 rounded-full ${petColors[pt.pet_type] || "bg-gray-400"}`} />
              <span className="capitalize text-sm font-medium text-[#2D4A3E]">
                {pt.pet_type?.replace('_', ' ')}
              </span>
            </div>
            <p className="text-lg font-bold text-[#2D4A3E]">{formatCurrency(pt.revenue)}</p>
            <p className="text-xs text-[#5C6D5E]">{pt.orders} orders</p>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-64"></div>
            <div className="grid grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-2xl"></div>
              ))}
            </div>
            <div className="h-64 bg-gray-200 rounded-2xl"></div>
          </div>
        </div>
      </div>
    );
  }

  const { summary, sales_trend, top_products, category_breakdown, pet_type_breakdown, recent_customers, acquisition_trend } = analytics || {};

  // Calculate trends (compare last 7 days to previous 7 days)
  const recentSales = sales_trend?.slice(-7) || [];
  const previousSales = sales_trend?.slice(-14, -7) || [];
  const recentRevenue = recentSales.reduce((sum, d) => sum + d.revenue, 0);
  const previousRevenue = previousSales.reduce((sum, d) => sum + d.revenue, 0);
  const revenueTrend = previousRevenue > 0 ? ((recentRevenue - previousRevenue) / previousRevenue) * 100 : 0;

  return (
    <AdminSidebar>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#2D4A3E] font-['Fraunces']" data-testid="page-title">
              Analytics
            </h1>
            <p className="text-sm text-[#5C6D5E]">Track store performance</p>
          </div>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[150px] rounded-full border-[#E8DFD5] text-sm">
              <Calendar className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="14">Last 14 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm" data-testid="revenue-card">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#6B8F71] rounded-lg sm:rounded-xl flex items-center justify-center">
                <DollarSign className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              {revenueTrend !== 0 && (
                <Badge className={`text-xs ${revenueTrend > 0 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                  {revenueTrend > 0 ? <ArrowUp className="w-3 h-3 mr-0.5" /> : <ArrowDown className="w-3 h-3 mr-0.5" />}
                  {Math.abs(revenueTrend).toFixed(0)}%
                </Badge>
              )}
            </div>
            <p className="text-xl sm:text-3xl font-bold text-[#2D4A3E]">{formatCurrency(summary?.total_revenue || 0)}</p>
            <p className="text-xs sm:text-sm text-[#5C6D5E]">Revenue</p>
          </div>

          <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm" data-testid="orders-card">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#2D4A3E] rounded-lg sm:rounded-xl flex items-center justify-center">
                <ShoppingBag className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
            </div>
            <p className="text-xl sm:text-3xl font-bold text-[#2D4A3E]">{summary?.total_orders || 0}</p>
            <p className="text-xs sm:text-sm text-[#5C6D5E]">Orders</p>
          </div>

          <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm" data-testid="customers-card">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#7CA5B8] rounded-lg sm:rounded-xl flex items-center justify-center">
                <Users className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
            </div>
            <p className="text-xl sm:text-3xl font-bold text-[#2D4A3E]">{summary?.total_customers || 0}</p>
            <p className="text-xs sm:text-sm text-[#5C6D5E]">Customers</p>
          </div>

          <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm" data-testid="aov-card">
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-[#D4A574] rounded-lg sm:rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
            </div>
            <p className="text-xl sm:text-3xl font-bold text-[#2D4A3E]">{formatCurrency(summary?.avg_order_value || 0)}</p>
            <p className="text-xs sm:text-sm text-[#5C6D5E]">Avg Order</p>
          </div>
        </div>

        {/* Sales Trend Chart */}
        <div className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm mb-6 sm:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 sm:mb-6">
            <div className="flex items-center gap-2 sm:gap-3">
              <BarChart3 className="w-4 h-4 sm:w-5 sm:h-5 text-[#2D4A3E]" />
              <h2 className="text-base sm:text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">Sales Trend</h2>
            </div>
            <p className="text-xs sm:text-sm text-[#5C6D5E]">
              {timeRange}d: {formatCurrency(sales_trend?.slice(-parseInt(timeRange)).reduce((s, d) => s + d.revenue, 0) || 0)}
            </p>
          </div>
          {sales_trend && <SalesChart data={sales_trend} />}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Top Products */}
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <Package className="w-5 h-5 text-[#2D4A3E]" />
              <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">Top Products</h2>
            </div>
            <div className="space-y-4">
              {top_products?.slice(0, 5).map((product, idx) => (
                <div key={product.id} className="flex items-center gap-4">
                  <div className="w-8 h-8 rounded-full bg-[#E8DFD5] flex items-center justify-center text-sm font-bold text-[#2D4A3E]">
                    {idx + 1}
                  </div>
                  <div className="w-12 h-12 rounded-lg bg-[#E8DFD5] overflow-hidden flex-shrink-0">
                    {product.image ? (
                      <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="w-5 h-5 text-[#5C6D5E]" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-[#2D4A3E] truncate">{product.name}</p>
                    <p className="text-sm text-[#5C6D5E]">{product.quantity} sold</p>
                  </div>
                  <p className="font-semibold text-[#2D4A3E]">{formatCurrency(product.revenue)}</p>
                </div>
              ))}
              {(!top_products || top_products.length === 0) && (
                <p className="text-center text-[#5C6D5E] py-8">No sales data yet</p>
              )}
            </div>
          </div>

          {/* Sales by Category */}
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <PieChart className="w-5 h-5 text-[#2D4A3E]" />
              <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">Sales by Category</h2>
            </div>
            {category_breakdown && category_breakdown.length > 0 ? (
              <CategoryChart data={category_breakdown} />
            ) : (
              <p className="text-center text-[#5C6D5E] py-8">No category data yet</p>
            )}
          </div>
        </div>

        {/* Pet Type Breakdown & Recent Customers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sales by Pet Type */}
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 className="w-5 h-5 text-[#2D4A3E]" />
              <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">Sales by Pet Type</h2>
            </div>
            {pet_type_breakdown && pet_type_breakdown.length > 0 ? (
              <PetTypeChart data={pet_type_breakdown} />
            ) : (
              <p className="text-center text-[#5C6D5E] py-8">No pet type data yet</p>
            )}
          </div>

          {/* Recent Customers */}
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <Users className="w-5 h-5 text-[#2D4A3E]" />
              <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">Recent Customers</h2>
            </div>
            <div className="space-y-3">
              {recent_customers?.slice(0, 6).map((customer) => (
                <div key={customer.id} className="flex items-center justify-between py-2 border-b border-[#E8DFD5] last:border-0">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#6B8F71] flex items-center justify-center text-white font-medium">
                      {customer.name?.charAt(0).toUpperCase() || "?"}
                    </div>
                    <div>
                      <p className="font-medium text-[#2D4A3E]">{customer.name}</p>
                      <p className="text-sm text-[#5C6D5E]">{customer.email}</p>
                    </div>
                  </div>
                  <p className="text-xs text-[#5C6D5E]">
                    {customer.created_at ? formatDate(customer.created_at) : ""}
                  </p>
                </div>
              ))}
              {(!recent_customers || recent_customers.length === 0) && (
                <p className="text-center text-[#5C6D5E] py-8">No customers yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </AdminSidebar>
  );
};

export default AdminAnalyticsPage;
