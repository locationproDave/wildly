import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";
import { 
  User, 
  Package, 
  Gift,
  ChevronRight
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AccountPage = () => {
  const { user, token, logout } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(response.data);
    } catch (error) {
      console.error("Error fetching orders:", error);
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

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-[#2D4A3E] mb-8 font-['Fraunces']">
          My Account
        </h1>

        {/* User Info */}
        <div className="bg-white rounded-2xl p-6 mb-8 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-[#2D4A3E] rounded-full flex items-center justify-center">
              <User className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[#2D4A3E]">{user?.name}</h2>
              <p className="text-[#5C6D5E]">{user?.email}</p>
            </div>
          </div>
          
          {user?.discount_code && (
            <div className="mt-6 p-4 bg-[#6B8F71]/10 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Gift className="w-5 h-5 text-[#6B8F71]" />
                <span className="font-semibold text-[#2D4A3E]">Your Discount Code</span>
              </div>
              <p className="text-lg font-mono font-bold text-[#6B8F71]">{user.discount_code}</p>
              <p className="text-sm text-[#5C6D5E] mt-1">15% off your first order</p>
            </div>
          )}
          
          <div className="mt-6 flex justify-end">
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

        {/* Orders */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-[#2D4A3E] mb-6 font-['Fraunces']">
            Order History
          </h2>

          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"></div>
              ))}
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-[#E8DFD5] rounded-full flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8 text-[#5C6D5E]" />
              </div>
              <h3 className="font-semibold text-[#2D4A3E] mb-2">No orders yet</h3>
              <p className="text-[#5C6D5E]">Your order history will appear here</p>
            </div>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => (
                <div
                  key={order.id}
                  className="border border-[#E8DFD5] rounded-xl p-4 hover:bg-[#FDF8F3] transition-colors"
                  data-testid={`order-${order.id}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <span className="font-semibold text-[#2D4A3E]">
                        {order.order_number}
                      </span>
                      <span className="text-sm text-[#5C6D5E] ml-3">
                        {new Date(order.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <Badge className={getStatusBadge(order.status)}>
                      {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex -space-x-2">
                      {order.items.slice(0, 3).map((item, i) => (
                        <img
                          key={i}
                          src={item.image || "https://via.placeholder.com/40"}
                          alt={item.product_name}
                          className="w-10 h-10 rounded-full border-2 border-white object-cover"
                        />
                      ))}
                      {order.items.length > 3 && (
                        <span className="w-10 h-10 rounded-full bg-[#E8DFD5] border-2 border-white flex items-center justify-center text-xs text-[#5C6D5E]">
                          +{order.items.length - 3}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-[#2D4A3E]">
                        ${order.total.toFixed(2)}
                      </span>
                      <ChevronRight className="w-5 h-5 text-[#5C6D5E]" />
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

export default AccountPage;
