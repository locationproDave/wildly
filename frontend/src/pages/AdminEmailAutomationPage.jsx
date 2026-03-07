import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import AdminSidebar from "../components/admin/AdminSidebar";
import { 
  ChevronLeft,
  Mail,
  ShoppingCart,
  Star,
  AlertTriangle,
  Send,
  CheckCircle,
  Clock,
  TrendingUp,
  Zap
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminEmailAutomationPage = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState({ abandoned: false, reviews: false, lowStock: false });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/admin/email-automation`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching email automation stats:", error);
      toast.error("Failed to load email automation data");
    } finally {
      setLoading(false);
    }
  };

  const sendAbandonedCartEmails = async () => {
    setSending(prev => ({ ...prev, abandoned: true }));
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/email-automation/send-abandoned`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      fetchStats();
    } catch (error) {
      toast.error("Failed to send abandoned cart emails");
    } finally {
      setSending(prev => ({ ...prev, abandoned: false }));
    }
  };

  const sendReviewRequestEmails = async () => {
    setSending(prev => ({ ...prev, reviews: true }));
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/email-automation/send-reviews`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      fetchStats();
    } catch (error) {
      toast.error("Failed to send review request emails");
    } finally {
      setSending(prev => ({ ...prev, reviews: false }));
    }
  };

  const sendLowStockAlerts = async () => {
    setSending(prev => ({ ...prev, lowStock: true }));
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/email-automation/send-low-stock`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      fetchStats();
    } catch (error) {
      toast.error("Failed to send low stock alerts");
    } finally {
      setSending(prev => ({ ...prev, lowStock: false }));
    }
  };

  if (loading) {
    return (
      <AdminSidebar>
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-64"></div>
          <div className="grid grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded-2xl"></div>
            ))}
          </div>
        </div>
      </AdminSidebar>
    );
  }

  return (
    <AdminSidebar>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[#2D4A3E] font-['Fraunces']" data-testid="page-title">
              Email Automation
            </h1>
            <p className="text-[#5C6D5E]">Automated email campaigns powered by AI</p>
          </div>
          <Badge className="bg-[#6B8F71] text-white px-4 py-2">
            <Zap className="w-4 h-4 mr-2" />
            AI Powered
          </Badge>
        </div>

        {/* Automation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Abandoned Cart Recovery */}
          <div className="bg-white rounded-2xl p-6 shadow-sm" data-testid="abandoned-cart-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                <ShoppingCart className="w-6 h-6 text-amber-600" />
              </div>
              <Badge className={stats?.automation_status?.abandoned_cart ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}>
                {stats?.automation_status?.abandoned_cart ? "Active" : "Inactive"}
              </Badge>
            </div>
            <h3 className="text-lg font-semibold text-[#2D4A3E] mb-2">Abandoned Cart Recovery</h3>
            <p className="text-sm text-[#5C6D5E] mb-4">
              Automatically remind customers about items left in their cart with a special discount.
            </p>
            
            <div className="bg-[#FDF8F3] rounded-xl p-4 mb-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-2xl font-bold text-[#2D4A3E]">{stats?.abandoned_carts?.pending || 0}</p>
                  <p className="text-xs text-[#5C6D5E]">Pending Carts</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-[#6B8F71]">{stats?.abandoned_carts?.recovery_rate || 0}%</p>
                  <p className="text-xs text-[#5C6D5E]">Recovery Rate</p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm text-[#5C6D5E] mb-4">
              <span className="flex items-center gap-1">
                <Mail className="w-4 h-4" />
                {stats?.abandoned_carts?.emails_sent || 0} emails sent
              </span>
              <span className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-600" />
                {stats?.abandoned_carts?.recovered || 0} recovered
              </span>
            </div>
            
            <Button 
              onClick={sendAbandonedCartEmails}
              disabled={sending.abandoned}
              className="w-full bg-amber-500 hover:bg-amber-600 rounded-full"
              data-testid="send-abandoned-btn"
            >
              {sending.abandoned ? (
                <>Sending...</>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Recovery Emails
                </>
              )}
            </Button>
          </div>

          {/* Review Requests */}
          <div className="bg-white rounded-2xl p-6 shadow-sm" data-testid="review-request-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <Star className="w-6 h-6 text-purple-600" />
              </div>
              <Badge className={stats?.automation_status?.review_request ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}>
                {stats?.automation_status?.review_request ? "Active" : "Inactive"}
              </Badge>
            </div>
            <h3 className="text-lg font-semibold text-[#2D4A3E] mb-2">Post-Purchase Reviews</h3>
            <p className="text-sm text-[#5C6D5E] mb-4">
              Request reviews from customers after their order is delivered, with bonus points incentive.
            </p>
            
            <div className="bg-[#FDF8F3] rounded-xl p-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-[#2D4A3E]">{stats?.review_requests?.eligible_orders || 0}</p>
                <p className="text-xs text-[#5C6D5E]">Orders eligible for review request</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center text-sm text-[#5C6D5E] mb-4">
              <Clock className="w-4 h-4 mr-1" />
              Sent 3 days after delivery
            </div>
            
            <Button 
              onClick={sendReviewRequestEmails}
              disabled={sending.reviews}
              className="w-full bg-purple-500 hover:bg-purple-600 rounded-full"
              data-testid="send-reviews-btn"
            >
              {sending.reviews ? (
                <>Sending...</>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Review Requests
                </>
              )}
            </Button>
          </div>

          {/* Low Stock Alerts */}
          <div className="bg-white rounded-2xl p-6 shadow-sm" data-testid="low-stock-card">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <Badge className={stats?.automation_status?.low_stock_alert ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}>
                {stats?.automation_status?.low_stock_alert ? "Active" : "Inactive"}
              </Badge>
            </div>
            <h3 className="text-lg font-semibold text-[#2D4A3E] mb-2">Low Stock Alerts</h3>
            <p className="text-sm text-[#5C6D5E] mb-4">
              Get notified when products are running low on inventory (below 10 units).
            </p>
            
            <div className="bg-[#FDF8F3] rounded-xl p-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{stats?.low_stock || 0}</p>
                <p className="text-xs text-[#5C6D5E]">Low stock products</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center text-sm text-[#5C6D5E] mb-4">
              <TrendingUp className="w-4 h-4 mr-1" />
              Threshold: 10 units
            </div>
            
            <Button 
              onClick={sendLowStockAlerts}
              disabled={sending.lowStock || (stats?.low_stock || 0) === 0}
              className="w-full bg-red-500 hover:bg-red-600 rounded-full"
              data-testid="send-low-stock-btn"
            >
              {sending.lowStock ? (
                <>Sending...</>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send Low Stock Alert
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Email Templates Preview */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces'] mb-6">
            Email Templates
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-[#E8DFD5] rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <ShoppingCart className="w-5 h-5 text-amber-600" />
                <span className="font-medium text-[#2D4A3E]">Abandoned Cart</span>
              </div>
              <div className="bg-[#FDF8F3] rounded-lg p-3 text-xs text-[#5C6D5E]">
                <p className="font-semibold mb-1">Subject: You left something behind! 🛒</p>
                <p>Includes cart items, total, and 10% discount code (COMEBACK10)</p>
              </div>
            </div>
            
            <div className="border border-[#E8DFD5] rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <Star className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-[#2D4A3E]">Review Request</span>
              </div>
              <div className="bg-[#FDF8F3] rounded-lg p-3 text-xs text-[#5C6D5E]">
                <p className="font-semibold mb-1">Subject: How's your pet loving it? ⭐</p>
                <p>Personalized with purchased product, offers 25 bonus points</p>
              </div>
            </div>
            
            <div className="border border-[#E8DFD5] rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <Mail className="w-5 h-5 text-[#6B8F71]" />
                <span className="font-medium text-[#2D4A3E]">Order Confirmation</span>
              </div>
              <div className="bg-[#FDF8F3] rounded-lg p-3 text-xs text-[#5C6D5E]">
                <p className="font-semibold mb-1">Subject: Order Confirmed! 🎉</p>
                <p>Order summary, items, totals, and loyalty points earned</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminSidebar>
  );
};

export default AdminEmailAutomationPage;
