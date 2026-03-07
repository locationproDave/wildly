import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  User, 
  Package, 
  Gift,
  ChevronRight,
  Award,
  Share2,
  Truck,
  Star,
  Settings,
  Mail,
  Lock,
  Pencil,
  Check,
  X,
  Eye,
  EyeOff,
  Loader2
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import OrderTracking from "../components/OrderTracking";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AccountPage = () => {
  const { user, token, logout, refreshUser } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loyalty, setLoyalty] = useState(null);
  const [referral, setReferral] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  
  // Profile editing state
  const [editMode, setEditMode] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [saving, setSaving] = useState(false);
  
  // Password change state
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);
  
  useEffect(() => {
    if (user) {
      setEditName(user.name || "");
      setEditEmail(user.email || "");
    }
  }, [user]);

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

  const handleSaveProfile = async () => {
    if (!editName.trim()) {
      toast.error("Name cannot be empty");
      return;
    }
    if (!editEmail.trim() || !editEmail.includes("@")) {
      toast.error("Please enter a valid email");
      return;
    }
    
    setSaving(true);
    try {
      const response = await axios.put(
        `${BACKEND_URL}/api/auth/profile`,
        { name: editName, email: editEmail },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success("Profile updated successfully!");
      setEditMode(false);
      
      // Refresh user data in context
      if (refreshUser) {
        await refreshUser();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword) {
      toast.error("Please enter your current password");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("New password must be at least 6 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New passwords don't match");
      return;
    }
    
    setChangingPassword(true);
    try {
      await axios.put(
        `${BACKEND_URL}/api/auth/password`,
        { current_password: currentPassword, new_password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success("Password changed successfully!");
      setPasswordDialog(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to change password");
    } finally {
      setChangingPassword(false);
    }
  };

  const cancelEdit = () => {
    setEditMode(false);
    setEditName(user?.name || "");
    setEditEmail(user?.email || "");
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

        {/* User Info Card with Edit */}
        <div className="bg-white rounded-2xl p-5 mb-5 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-[#2D4A3E] rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-white" />
              </div>
              {editMode ? (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-[#5C6D5E] mb-1 block">Name</label>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="h-9 w-64 rounded-lg"
                      placeholder="Your name"
                      data-testid="edit-name-input"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-[#5C6D5E] mb-1 block">Email</label>
                    <Input
                      type="email"
                      value={editEmail}
                      onChange={(e) => setEditEmail(e.target.value)}
                      className="h-9 w-64 rounded-lg"
                      placeholder="your@email.com"
                      data-testid="edit-email-input"
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="text-xl font-semibold text-[#2D4A3E]">{user?.name}</h2>
                  <p className="text-[#5C6D5E] flex items-center gap-1">
                    <Mail className="w-4 h-4" />
                    {user?.email}
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {editMode ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={cancelEdit}
                    className="rounded-full"
                    disabled={saving}
                  >
                    <X className="w-4 h-4 mr-1" />
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveProfile}
                    className="rounded-full bg-[#2D4A3E] hover:bg-[#1F342B]"
                    disabled={saving}
                    data-testid="save-profile-btn"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4 mr-1" />
                    )}
                    Save
                  </Button>
                </>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditMode(true)}
                  className="rounded-full"
                  data-testid="edit-profile-btn"
                >
                  <Pencil className="w-4 h-4 mr-1" />
                  Edit Profile
                </Button>
              )}
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2 pt-4 border-t border-[#E8E6DE]">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPasswordDialog(true)}
              className="rounded-full"
              data-testid="change-password-btn"
            >
              <Lock className="w-4 h-4 mr-2" />
              Change Password
            </Button>
            <Button
              variant="outline"
              onClick={logout}
              size="sm"
              className="rounded-full text-red-600 hover:text-red-700 hover:bg-red-50"
              data-testid="logout-btn"
            >
              Sign Out
            </Button>
          </div>
        </div>

        {/* Tabs for Orders and More */}
        <Tabs defaultValue="orders" className="space-y-4">
          <TabsList className="bg-white rounded-full p-1 border border-[#E8E6DE]">
            <TabsTrigger value="orders" className="rounded-full data-[state=active]:bg-[#2D4A3E] data-[state=active]:text-white">
              <Package className="w-4 h-4 mr-2" />
              Orders
            </TabsTrigger>
            <TabsTrigger value="rewards" className="rounded-full data-[state=active]:bg-[#2D4A3E] data-[state=active]:text-white">
              <Award className="w-4 h-4 mr-2" />
              Rewards
            </TabsTrigger>
            <TabsTrigger value="referral" className="rounded-full data-[state=active]:bg-[#2D4A3E] data-[state=active]:text-white">
              <Share2 className="w-4 h-4 mr-2" />
              Referral
            </TabsTrigger>
          </TabsList>
          
          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-4">
            {loading ? (
              <div className="bg-white rounded-2xl p-10 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#5C6D5E] mx-auto" />
                <p className="text-[#5C6D5E] mt-2">Loading orders...</p>
              </div>
            ) : orders.length === 0 ? (
              <div className="bg-white rounded-2xl p-10 text-center shadow-sm">
                <Package className="w-16 h-16 mx-auto text-[#D4D4D4] mb-4" />
                <h3 className="text-lg font-semibold text-[#2D4A3E] mb-2">No orders yet</h3>
                <p className="text-[#5C6D5E] mb-4">Start shopping to see your orders here</p>
                <Link to="/products">
                  <Button className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full">
                    Browse Products
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {orders.map((order) => (
                  <div
                    key={order.id}
                    className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => setSelectedOrder(order)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-[#2D4A3E]">{order.order_number}</p>
                        <p className="text-sm text-[#5C6D5E]">
                          {new Date(order.created_at).toLocaleDateString()} • {order.items?.length} items
                        </p>
                      </div>
                      <div className="text-right flex items-center gap-3">
                        <div>
                          <p className="font-semibold text-[#2D4A3E]">${order.total?.toFixed(2)}</p>
                          <Badge className={`${getStatusBadge(order.status)} capitalize`}>
                            {order.status}
                          </Badge>
                        </div>
                        <ChevronRight className="w-5 h-5 text-[#5C6D5E]" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
          
          {/* Rewards Tab */}
          <TabsContent value="rewards">
            {loyalty ? (
              <div className="bg-white rounded-2xl p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-3 rounded-full ${getTierColor(loyalty.tier)}`}>
                    <Award className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#2D4A3E] capitalize">{loyalty.tier} Member</h3>
                    <p className="text-sm text-[#5C6D5E]">{loyalty.points} points earned</p>
                  </div>
                </div>
                <div className="bg-[#F8F7F4] rounded-xl p-4">
                  <p className="text-sm text-[#5C6D5E]">
                    {loyalty.points_to_next_tier > 0 
                      ? `Earn ${loyalty.points_to_next_tier} more points to reach ${loyalty.next_tier}`
                      : "You've reached the highest tier!"}
                  </p>
                  <div className="mt-2 h-2 bg-[#E8E6DE] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[#2D4A3E] rounded-full transition-all"
                      style={{ width: `${Math.min(100, (loyalty.points / (loyalty.points + loyalty.points_to_next_tier)) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl p-10 text-center shadow-sm">
                <Award className="w-16 h-16 mx-auto text-[#D4D4D4] mb-4" />
                <h3 className="text-lg font-semibold text-[#2D4A3E] mb-2">Join Our Rewards Program</h3>
                <p className="text-[#5C6D5E]">Earn points with every purchase</p>
              </div>
            )}
          </TabsContent>
          
          {/* Referral Tab */}
          <TabsContent value="referral">
            <div className="bg-white rounded-2xl p-5 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-full bg-[#6B8F71]/10">
                  <Gift className="w-6 h-6 text-[#6B8F71]" />
                </div>
                <div>
                  <h3 className="font-semibold text-[#2D4A3E]">Refer & Earn</h3>
                  <p className="text-sm text-[#5C6D5E]">Give $10, Get $10</p>
                </div>
              </div>
              {referral?.code && (
                <div className="bg-[#F8F7F4] rounded-xl p-4">
                  <p className="text-xs text-[#5C6D5E] mb-2">Your referral code</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-white px-4 py-2 rounded-lg font-mono text-[#2D4A3E] border border-[#E8E6DE]">
                      {referral.code}
                    </code>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(referral.code);
                        toast.success("Code copied!");
                      }}
                      className="rounded-lg"
                    >
                      Copy
                    </Button>
                  </div>
                  <p className="text-sm text-[#5C6D5E] mt-3">
                    Referrals: {referral.referral_count || 0} • Earned: ${referral.total_earned || 0}
                  </p>
                </div>
              )}
              <Link to="/referral" className="block mt-4">
                <Button variant="outline" className="w-full rounded-full">
                  Learn More
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </TabsContent>
        </Tabs>

        {/* Order Tracking Modal */}
        {selectedOrder && (
          <OrderTracking 
            order={selectedOrder}
            onClose={() => setSelectedOrder(null)}
          />
        )}

        {/* Password Change Dialog */}
        <Dialog open={passwordDialog} onOpenChange={setPasswordDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="font-['Fraunces']">Change Password</DialogTitle>
              <DialogDescription>
                Enter your current password and choose a new one.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                  Current Password
                </label>
                <div className="relative">
                  <Input
                    type={showCurrentPassword ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="pr-10 rounded-xl"
                    placeholder="Enter current password"
                    data-testid="current-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5C6D5E]"
                  >
                    {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                  New Password
                </label>
                <div className="relative">
                  <Input
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="pr-10 rounded-xl"
                    placeholder="Enter new password (min 6 chars)"
                    data-testid="new-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5C6D5E]"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                  Confirm New Password
                </label>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="rounded-xl"
                  placeholder="Confirm new password"
                  data-testid="confirm-password-input"
                />
              </div>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setPasswordDialog(false)}
                className="rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleChangePassword}
                disabled={changingPassword}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
                data-testid="submit-password-btn"
              >
                {changingPassword ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Changing...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4 mr-2" />
                    Change Password
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AccountPage;
