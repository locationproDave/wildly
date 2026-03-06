import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { 
  User, 
  Package, 
  Gift,
  ChevronRight,
  Award,
  Share2,
  Truck,
  Star
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import OrderTracking from "../components/OrderTracking";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AccountPage = () => {
  const { user, token, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loyalty, setLoyalty] = useState(null);
  const [referral, setReferral] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, loyaltyRes, referralRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/orders`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/loyalty/status`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: null })),
        axios.get(`${BACKEND_URL}/api/referral/code`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: null }))
      ]);
      setOrders(ordersRes.data);
      setLoyalty(loyaltyRes.data);
      setReferral(referralRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
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

  const getTierColor = (tier) => {
    const colors = {
      bronze: "text-amber-700 bg-amber-100",
      silver: "text-gray-600 bg-gray-200",
      gold: "text-yellow-600 bg-yellow-100",
      platinum: "text-purple-600 bg-purple-100"
    };
    return colors[tier] || colors.bronze;
  };

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-[#2D4A3E] mb-5 font-['Fraunces']">
          My Account
        </h1>

        {/* User Info Card */}
        <div className="bg-white rounded-2xl p-5 mb-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-[#2D4A3E] rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-[#2D4A3E]">{user?.name}</h2>
                <p className="text-[#5C6D5E]">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={logout}
              className="rounded-full"
              data-testid="logout-btn"
            >
              Sign Out
            </Button>
          </div>
        </div>

        {/* Loyalty & Referral Cards */}
        <div className="grid md:grid-cols-2 gap-5 mb-5">
          {/* Loyalty Status */}
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[#2D4A3E] flex items-center gap-2">
                <Award className="w-5 h-5 text-[#D4A574]" />
                Rewards
              </h3>
              {loyalty && (
                <Badge className={`${getTierColor(loyalty.tier)} capitalize`}>
                  {loyalty.tier}
                </Badge>
              )}
            </div>
            {loyalty ? (
              <div>
                <div className="text-3xl font-bold text-[#2D4A3E] mb-1">
                  {loyalty.points} pts
                </div>
                <p className="text-sm text-[#5C6D5E] mb-3">
                  Lifetime: {loyalty.lifetime_points} points
                </p>
                {loyalty.next_tier && (
                  <div className="text-sm text-[#5C6D5E]">
                    <div className="flex justify-between mb-1">
                      <span>Progress to {loyalty.next_tier}</span>
                      <span>{loyalty.points_to_next_tier} pts to go</span>
                    </div>
                    <div className="h-2 bg-[#E8DFD5] rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[#D4A574]"
                        style={{ 
                          width: `${Math.min(100, ((loyalty.lifetime_points) / (loyalty.lifetime_points + loyalty.points_to_next_tier)) * 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                )}
                <p className="text-xs text-[#6B8F71] mt-3">
                  100 pts = $5 off • Earn {loyalty.tier_benefits?.points_multiplier}x points on orders
                </p>
              </div>
            ) : (
              <p className="text-[#5C6D5E]">Loading rewards...</p>
            )}
          </div>

          {/* Referral */}
          <div className="bg-gradient-to-br from-[#2D4A3E] to-[#3D5A4E] rounded-2xl p-6 text-white">
            <div className="flex items-center gap-2 mb-4">
              <Share2 className="w-5 h-5" />
              <h3 className="font-semibold">Give $10, Get $10</h3>
            </div>
            {referral ? (
              <div>
                <p className="text-white/80 text-sm mb-3">
                  Share your code and earn rewards when friends order!
                </p>
                <div className="bg-white/10 rounded-xl p-3 mb-3">
                  <p className="text-xs text-white/70">Your Code</p>
                  <p className="font-bold font-mono text-lg">{referral.referral_code}</p>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>{referral.completed_referrals} referrals • ${referral.total_earned} earned</span>
                  <Link to="/referral">
                    <Button size="sm" className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] rounded-full">
                      Share
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <p className="text-white/80">Loading referral info...</p>
            )}
          </div>
        </div>

        {/* Orders Section */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#E8DFD5]">
            <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">
              Order History
            </h2>
          </div>

          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"></div>
              ))}
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-12 px-6">
              <div className="w-16 h-16 bg-[#E8DFD5] rounded-full flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8 text-[#5C6D5E]" />
              </div>
              <h3 className="font-semibold text-[#2D4A3E] mb-2">No orders yet</h3>
              <p className="text-[#5C6D5E] mb-4">Your order history will appear here</p>
              <Link to="/products">
                <Button className="rounded-full">Start Shopping</Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-[#E8DFD5]">
              {orders.map((order) => (
                <div key={order.id}>
                  <div
                    className="p-6 hover:bg-[#FDF8F3] transition-colors cursor-pointer"
                    onClick={() => setSelectedOrder(selectedOrder === order.id ? null : order.id)}
                    data-testid={`order-${order.id}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-[#2D4A3E]">
                          {order.order_number}
                        </span>
                        <span className="text-sm text-[#5C6D5E]">
                          {new Date(order.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={getStatusBadge(order.status)}>
                          {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                        </Badge>
                        {order.tracking && (
                          <Badge className="bg-purple-100 text-purple-800">
                            <Truck className="w-3 h-3 mr-1" />
                            Tracking
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex -space-x-2">
                        {order.items.slice(0, 4).map((item, i) => (
                          <img
                            key={i}
                            src={item.image || "https://via.placeholder.com/40"}
                            alt={item.product_name}
                            className="w-10 h-10 rounded-full border-2 border-white object-cover"
                          />
                        ))}
                        {order.items.length > 4 && (
                          <span className="w-10 h-10 rounded-full bg-[#E8DFD5] border-2 border-white flex items-center justify-center text-xs text-[#5C6D5E]">
                            +{order.items.length - 4}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-[#2D4A3E]">
                          ${order.total.toFixed(2)}
                        </span>
                        <ChevronRight className={`w-5 h-5 text-[#5C6D5E] transition-transform ${selectedOrder === order.id ? 'rotate-90' : ''}`} />
                      </div>
                    </div>
                  </div>
                  
                  {/* Order Details & Tracking */}
                  {selectedOrder === order.id && (
                    <div className="px-6 pb-6 pt-0">
                      <div className="border-t border-[#E8DFD5] pt-6">
                        {/* Order Items */}
                        <div className="mb-6">
                          <h4 className="text-sm font-semibold text-[#2D4A3E] mb-3">Order Items</h4>
                          <div className="space-y-2">
                            {order.items.map((item, idx) => (
                              <div key={idx} className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-3">
                                  <img 
                                    src={item.image || "https://via.placeholder.com/32"} 
                                    alt={item.product_name}
                                    className="w-8 h-8 rounded object-cover"
                                  />
                                  <span className="text-[#2D4A3E]">{item.product_name}</span>
                                  <span className="text-[#5C6D5E]">x{item.quantity}</span>
                                </div>
                                <span className="text-[#2D4A3E]">${(item.price * item.quantity).toFixed(2)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        {/* Order Tracking */}
                        <OrderTracking orderId={order.id} orderStatus={order.status} />
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AccountPage;
