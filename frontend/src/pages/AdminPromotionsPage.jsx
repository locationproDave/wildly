import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  Tag, 
  Plus, 
  Trash2, 
  Calendar,
  DollarSign,
  Percent,
  Truck,
  CheckCircle,
  XCircle,
  ChevronLeft,
  Users,
  Gift
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminPromotionsPage = () => {
  const { token } = useAuth();
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    description: "",
    discount_type: "percentage",
    discount_value: "",
    min_purchase: "0",
    max_uses: "",
    is_first_order_only: false,
    valid_days: "30"
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchPromotions();
  }, []);

  const fetchPromotions = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/admin/promotions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPromotions(response.data);
    } catch (error) {
      console.error("Error fetching promotions:", error);
      toast.error("Failed to load promotions");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePromotion = async (e) => {
    e.preventDefault();
    
    if (!formData.code || !formData.name || !formData.discount_value) {
      toast.error("Please fill in all required fields");
      return;
    }

    setSubmitting(true);
    try {
      const params = new URLSearchParams({
        code: formData.code,
        name: formData.name,
        description: formData.description || formData.name,
        discount_type: formData.discount_type,
        discount_value: formData.discount_value,
        min_purchase: formData.min_purchase || "0",
        is_first_order_only: formData.is_first_order_only,
        valid_days: formData.valid_days || "30"
      });
      
      if (formData.max_uses) {
        params.append("max_uses", formData.max_uses);
      }

      await axios.post(
        `${BACKEND_URL}/api/admin/promotions?${params.toString()}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success("Promotion created successfully!");
      setIsDialogOpen(false);
      setFormData({
        code: "",
        name: "",
        description: "",
        discount_type: "percentage",
        discount_value: "",
        min_purchase: "0",
        max_uses: "",
        is_first_order_only: false,
        valid_days: "30"
      });
      fetchPromotions();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create promotion");
    } finally {
      setSubmitting(false);
    }
  };

  const getDiscountIcon = (type) => {
    switch (type) {
      case "percentage":
        return <Percent className="w-4 h-4" />;
      case "fixed_amount":
        return <DollarSign className="w-4 h-4" />;
      case "free_shipping":
        return <Truck className="w-4 h-4" />;
      default:
        return <Tag className="w-4 h-4" />;
    }
  };

  const formatDiscount = (promo) => {
    switch (promo.discount_type) {
      case "percentage":
        return `${promo.discount_value}% off`;
      case "fixed_amount":
        return `$${promo.discount_value} off`;
      case "free_shipping":
        return "Free shipping";
      default:
        return promo.discount_value;
    }
  };

  const isExpired = (promo) => {
    if (!promo.valid_until) return false;
    return new Date(promo.valid_until) < new Date();
  };

  const isMaxedOut = (promo) => {
    if (!promo.max_uses) return false;
    return promo.uses_count >= promo.max_uses;
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link 
          to="/admin" 
          className="inline-flex items-center text-[#5C6D5E] hover:text-[#2D4A3E] mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#2D4A3E] font-['Fraunces']">
              Promotions
            </h1>
            <p className="text-[#5C6D5E]">Manage discount codes and special offers</p>
          </div>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
                data-testid="create-promo-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Promotion
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle className="text-[#2D4A3E] font-['Fraunces']">
                  Create New Promotion
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreatePromotion} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="code">Promo Code *</Label>
                    <Input
                      id="code"
                      value={formData.code}
                      onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                      placeholder="SUMMER20"
                      className="mt-1"
                      data-testid="promo-code-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="Summer Sale"
                      className="mt-1"
                      data-testid="promo-name-input"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="20% off all summer products"
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Discount Type *</Label>
                    <Select
                      value={formData.discount_type}
                      onValueChange={(value) => setFormData({...formData, discount_type: value})}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">Percentage (%)</SelectItem>
                        <SelectItem value="fixed_amount">Fixed Amount ($)</SelectItem>
                        <SelectItem value="free_shipping">Free Shipping</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="discount_value">
                      {formData.discount_type === "percentage" ? "Percentage *" : "Amount *"}
                    </Label>
                    <Input
                      id="discount_value"
                      type="number"
                      value={formData.discount_value}
                      onChange={(e) => setFormData({...formData, discount_value: e.target.value})}
                      placeholder={formData.discount_type === "percentage" ? "20" : "10"}
                      className="mt-1"
                      disabled={formData.discount_type === "free_shipping"}
                      data-testid="promo-value-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="min_purchase">Min. Purchase ($)</Label>
                    <Input
                      id="min_purchase"
                      type="number"
                      value={formData.min_purchase}
                      onChange={(e) => setFormData({...formData, min_purchase: e.target.value})}
                      placeholder="0"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="max_uses">Max Uses (optional)</Label>
                    <Input
                      id="max_uses"
                      type="number"
                      value={formData.max_uses}
                      onChange={(e) => setFormData({...formData, max_uses: e.target.value})}
                      placeholder="Unlimited"
                      className="mt-1"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="valid_days">Valid For (days)</Label>
                    <Input
                      id="valid_days"
                      type="number"
                      value={formData.valid_days}
                      onChange={(e) => setFormData({...formData, valid_days: e.target.value})}
                      placeholder="30"
                      className="mt-1"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_first_order_only}
                        onChange={(e) => setFormData({...formData, is_first_order_only: e.target.checked})}
                        className="rounded border-[#E8DFD5]"
                      />
                      <span className="text-sm text-[#2D4A3E]">First order only</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="bg-[#2D4A3E] hover:bg-[#1F342B]"
                    data-testid="submit-promo-btn"
                  >
                    {submitting ? "Creating..." : "Create Promotion"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#6B8F71] rounded-xl flex items-center justify-center text-white">
                <Tag className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-[#2D4A3E]">{promotions.length}</p>
                <p className="text-sm text-[#5C6D5E]">Total Promotions</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#2D4A3E] rounded-xl flex items-center justify-center text-white">
                <CheckCircle className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-[#2D4A3E]">
                  {promotions.filter(p => p.is_active && !isExpired(p) && !isMaxedOut(p)).length}
                </p>
                <p className="text-sm text-[#5C6D5E]">Active</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#D4A574] rounded-xl flex items-center justify-center text-white">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-[#2D4A3E]">
                  {promotions.reduce((sum, p) => sum + (p.uses_count || 0), 0)}
                </p>
                <p className="text-sm text-[#5C6D5E]">Total Uses</p>
              </div>
            </div>
          </div>
        </div>

        {/* Promotions List */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[#E8DFD5]">
            <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">
              All Promotions
            </h2>
          </div>

          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : promotions.length === 0 ? (
            <div className="p-12 text-center">
              <Gift className="w-12 h-12 text-[#5C6D5E] mx-auto mb-4" />
              <p className="text-[#5C6D5E]">No promotions yet. Create your first one!</p>
            </div>
          ) : (
            <div className="divide-y divide-[#E8DFD5]">
              {promotions.map((promo) => {
                const expired = isExpired(promo);
                const maxedOut = isMaxedOut(promo);
                const isActive = promo.is_active && !expired && !maxedOut;
                
                return (
                  <div 
                    key={promo.id} 
                    className={`p-6 hover:bg-[#FDF8F3] transition-colors ${!isActive ? 'opacity-60' : ''}`}
                    data-testid={`promo-row-${promo.code}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          isActive ? 'bg-[#6B8F71]/10 text-[#6B8F71]' : 'bg-gray-100 text-gray-400'
                        }`}>
                          {getDiscountIcon(promo.discount_type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-bold text-[#2D4A3E] font-mono">{promo.code}</p>
                            {promo.is_first_order_only && (
                              <Badge className="bg-[#D4A574]/10 text-[#D4A574] text-xs">
                                First Order
                              </Badge>
                            )}
                            {promo.is_loyalty_reward && (
                              <Badge className="bg-[#7CA5B8]/10 text-[#7CA5B8] text-xs">
                                Loyalty
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-[#5C6D5E]">{promo.name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="font-semibold text-[#2D4A3E]">{formatDiscount(promo)}</p>
                          {promo.min_purchase > 0 && (
                            <p className="text-xs text-[#5C6D5E]">Min ${promo.min_purchase}</p>
                          )}
                        </div>
                        
                        <div className="text-center">
                          <p className="font-semibold text-[#2D4A3E]">
                            {promo.uses_count || 0}{promo.max_uses ? `/${promo.max_uses}` : ''}
                          </p>
                          <p className="text-xs text-[#5C6D5E]">Uses</p>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {isActive ? (
                            <Badge className="bg-[#6B8F71]/10 text-[#6B8F71]">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Active
                            </Badge>
                          ) : expired ? (
                            <Badge className="bg-red-100 text-red-800">
                              <XCircle className="w-3 h-3 mr-1" />
                              Expired
                            </Badge>
                          ) : maxedOut ? (
                            <Badge className="bg-yellow-100 text-yellow-800">
                              <XCircle className="w-3 h-3 mr-1" />
                              Max Used
                            </Badge>
                          ) : (
                            <Badge className="bg-gray-100 text-gray-600">
                              <XCircle className="w-3 h-3 mr-1" />
                              Inactive
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPromotionsPage;
