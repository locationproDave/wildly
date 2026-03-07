import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import AdminSidebar from "../components/admin/AdminSidebar";
import { 
  Package, 
  ChevronLeft,
  ChevronRight,
  Clock,
  Truck,
  CheckCircle,
  X,
  Mail,
  MapPin,
  CreditCard,
  Calendar,
  Eye,
  Send
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Label } from "../components/ui/label";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  pending: { color: "bg-yellow-100 text-yellow-800", icon: Clock, label: "Pending" },
  processing: { color: "bg-blue-100 text-blue-800", icon: Package, label: "Processing" },
  shipped: { color: "bg-purple-100 text-purple-800", icon: Truck, label: "Shipped" },
  delivered: { color: "bg-green-100 text-green-800", icon: CheckCircle, label: "Delivered" },
  cancelled: { color: "bg-red-100 text-red-800", icon: X, label: "Cancelled" }
};

const CARRIERS = [
  { value: "usps", label: "USPS" },
  { value: "fedex", label: "FedEx" },
  { value: "ups", label: "UPS" },
  { value: "dhl", label: "DHL" }
];

const AdminOrdersPage = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showTrackingDialog, setShowTrackingDialog] = useState(false);
  const [trackingOrder, setTrackingOrder] = useState(null);
  const [trackingData, setTrackingData] = useState({ carrier: "usps", tracking_number: "" });
  const [savingTracking, setSavingTracking] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const fetchOrders = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const response = await axios.get(`${BACKEND_URL}/api/admin/orders${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(response.data);
    } catch (error) {
      console.error("Error fetching orders:", error);
      toast.error("Failed to load orders");
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
      toast.success(`Order marked as ${status}`);
      fetchOrders();
    } catch (error) {
      console.error("Error updating order:", error);
      toast.error("Failed to update order");
    }
  };

  const openTrackingDialog = (order) => {
    setTrackingOrder(order);
    setTrackingData({ carrier: "usps", tracking_number: "" });
    setShowTrackingDialog(true);
  };

  const addTracking = async () => {
    if (!trackingData.tracking_number) {
      toast.error("Please enter a tracking number");
      return;
    }
    
    setSavingTracking(true);
    try {
      await axios.post(
        `${BACKEND_URL}/api/admin/orders/${trackingOrder.id}/tracking?carrier=${trackingData.carrier}&tracking_number=${trackingData.tracking_number}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Tracking information added");
      setShowTrackingDialog(false);
      fetchOrders();
    } catch (error) {
      console.error("Error adding tracking:", error);
      toast.error("Failed to add tracking");
    } finally {
      setSavingTracking(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const orderCounts = {
    all: orders.length,
    pending: orders.filter(o => o.status === "pending").length,
    processing: orders.filter(o => o.status === "processing").length,
    shipped: orders.filter(o => o.status === "shipped").length
  };

  return (
    <AdminSidebar>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-[#2D4A3E] font-['Fraunces']" data-testid="page-title">
            Order Management
          </h1>
          <p className="text-[#5C6D5E]">{orders.length} total orders</p>
        </div>

        {/* Status Filters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${statusFilter === "" ? "ring-2 ring-[#2D4A3E]" : ""}`}
            onClick={() => setStatusFilter("")}
            data-testid="filter-all"
          >
            <div className="flex items-center gap-3">
              <Package className="w-5 h-5 text-[#5C6D5E]" />
              <span className="font-medium text-[#2D4A3E]">All Orders</span>
              <span className="ml-auto bg-[#E8DFD5] px-2 py-1 rounded-full text-sm">{orderCounts.all}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${statusFilter === "pending" ? "ring-2 ring-yellow-500" : ""}`}
            onClick={() => setStatusFilter("pending")}
            data-testid="filter-pending"
          >
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-yellow-600" />
              <span className="font-medium text-[#2D4A3E]">Pending</span>
              <span className="ml-auto bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-sm">{orderCounts.pending}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${statusFilter === "processing" ? "ring-2 ring-blue-500" : ""}`}
            onClick={() => setStatusFilter("processing")}
            data-testid="filter-processing"
          >
            <div className="flex items-center gap-3">
              <Package className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-[#2D4A3E]">Processing</span>
              <span className="ml-auto bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">{orderCounts.processing}</span>
            </div>
          </div>
          <div 
            className={`bg-white rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${statusFilter === "shipped" ? "ring-2 ring-purple-500" : ""}`}
            onClick={() => setStatusFilter("shipped")}
            data-testid="filter-shipped"
          >
            <div className="flex items-center gap-3">
              <Truck className="w-5 h-5 text-purple-600" />
              <span className="font-medium text-[#2D4A3E]">Shipped</span>
              <span className="ml-auto bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-sm">{orderCounts.shipped}</span>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-100 rounded animate-pulse"></div>
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
                <div 
                  key={order.id} 
                  className="p-4 hover:bg-[#FDF8F3] transition-colors"
                  data-testid={`order-row-${order.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      {/* Order Info */}
                      <div className="min-w-[140px]">
                        <p className="font-semibold text-[#2D4A3E]">{order.order_number}</p>
                        <div className="flex items-center gap-1 text-xs text-[#5C6D5E]">
                          <Calendar className="w-3 h-3" />
                          {formatDate(order.created_at)}
                        </div>
                      </div>
                      
                      {/* Customer */}
                      <div className="min-w-[180px]">
                        <div className="flex items-center gap-1 text-sm text-[#2D4A3E]">
                          <Mail className="w-3 h-3" />
                          {order.email}
                        </div>
                        {order.shipping_address && (
                          <div className="flex items-center gap-1 text-xs text-[#5C6D5E]">
                            <MapPin className="w-3 h-3" />
                            {order.shipping_address.city}, {order.shipping_address.state}
                          </div>
                        )}
                      </div>
                      
                      {/* Items */}
                      <div className="min-w-[100px]">
                        <p className="text-sm text-[#2D4A3E]">
                          {order.items?.length || 0} item{(order.items?.length || 0) !== 1 ? "s" : ""}
                        </p>
                        <p className="text-xs text-[#5C6D5E]">
                          {order.items?.slice(0, 2).map(i => i.product_name).join(", ")}
                          {(order.items?.length || 0) > 2 ? "..." : ""}
                        </p>
                      </div>
                      
                      {/* Total */}
                      <div className="min-w-[80px]">
                        <p className="font-semibold text-[#2D4A3E]">${order.total?.toFixed(2)}</p>
                        <div className="flex items-center gap-1 text-xs text-green-600">
                          <CreditCard className="w-3 h-3" />
                          {order.payment_status}
                        </div>
                      </div>
                      
                      {/* Tracking */}
                      <div className="min-w-[100px]">
                        {order.tracking ? (
                          <div className="text-xs">
                            <p className="text-[#2D4A3E] font-medium capitalize">{order.tracking.carrier}</p>
                            <p className="text-[#5C6D5E]">{order.tracking.tracking_number}</p>
                          </div>
                        ) : order.status !== "cancelled" && order.status !== "delivered" ? (
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="text-xs rounded-full"
                            onClick={() => openTrackingDialog(order)}
                            data-testid={`add-tracking-${order.id}`}
                          >
                            <Send className="w-3 h-3 mr-1" />
                            Add Tracking
                          </Button>
                        ) : (
                          <span className="text-xs text-[#5C6D5E]">-</span>
                        )}
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-3">
                      {getStatusBadge(order.status)}
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="outline" size="sm" className="rounded-full">
                            Update
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "pending")}>
                            <Clock className="w-4 h-4 mr-2 text-yellow-600" />
                            Mark as Pending
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "processing")}>
                            <Package className="w-4 h-4 mr-2 text-blue-600" />
                            Mark as Processing
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "shipped")}>
                            <Truck className="w-4 h-4 mr-2 text-purple-600" />
                            Mark as Shipped
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => updateOrderStatus(order.id, "delivered")}>
                            <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                            Mark as Delivered
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => updateOrderStatus(order.id, "cancelled")}
                            className="text-red-600"
                          >
                            <X className="w-4 h-4 mr-2" />
                            Cancel Order
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      
                      <Button 
                        variant="ghost" 
                        size="icon"
                        className="rounded-full"
                        onClick={() => setSelectedOrder(order)}
                        data-testid={`view-order-${order.id}`}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Order Details Dialog */}
        <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E] font-['Fraunces']">
                Order {selectedOrder?.order_number}
              </DialogTitle>
              <DialogDescription>
                Placed on {selectedOrder && formatDate(selectedOrder.created_at)}
              </DialogDescription>
            </DialogHeader>
            
            {selectedOrder && (
              <div className="space-y-6 py-4">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <span className="text-[#5C6D5E]">Status</span>
                  {getStatusBadge(selectedOrder.status)}
                </div>
                
                {/* Customer */}
                <div className="bg-[#FDF8F3] rounded-xl p-4">
                  <h4 className="font-semibold text-[#2D4A3E] mb-2">Customer</h4>
                  <p className="text-sm">{selectedOrder.email}</p>
                  {selectedOrder.shipping_address && (
                    <div className="mt-2 text-sm text-[#5C6D5E]">
                      <p>{selectedOrder.shipping_address.name}</p>
                      <p>{selectedOrder.shipping_address.address_line1}</p>
                      {selectedOrder.shipping_address.address_line2 && (
                        <p>{selectedOrder.shipping_address.address_line2}</p>
                      )}
                      <p>
                        {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}
                      </p>
                    </div>
                  )}
                </div>
                
                {/* Items */}
                <div>
                  <h4 className="font-semibold text-[#2D4A3E] mb-2">Items</h4>
                  <div className="space-y-2">
                    {selectedOrder.items?.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-white border border-[#E8DFD5] rounded-lg">
                        <div className="flex items-center gap-3">
                          {item.image && (
                            <img src={item.image} alt={item.product_name} className="w-12 h-12 rounded-lg object-cover" />
                          )}
                          <div>
                            <p className="font-medium text-[#2D4A3E]">{item.product_name}</p>
                            <p className="text-sm text-[#5C6D5E]">Qty: {item.quantity}</p>
                          </div>
                        </div>
                        <p className="font-semibold text-[#2D4A3E]">${(item.price * item.quantity).toFixed(2)}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Totals */}
                <div className="border-t border-[#E8DFD5] pt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[#5C6D5E]">Subtotal</span>
                    <span>${selectedOrder.subtotal?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[#5C6D5E]">Shipping</span>
                    <span>${selectedOrder.shipping_cost?.toFixed(2) || "0.00"}</span>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-[#5C6D5E]">Tax</span>
                    <span>${selectedOrder.tax?.toFixed(2) || "0.00"}</span>
                  </div>
                  <div className="flex justify-between font-semibold text-lg">
                    <span className="text-[#2D4A3E]">Total</span>
                    <span className="text-[#2D4A3E]">${selectedOrder.total?.toFixed(2)}</span>
                  </div>
                </div>
                
                {/* Tracking */}
                {selectedOrder.tracking && (
                  <div className="bg-purple-50 rounded-xl p-4">
                    <h4 className="font-semibold text-[#2D4A3E] mb-2">Tracking</h4>
                    <p className="text-sm capitalize"><strong>Carrier:</strong> {selectedOrder.tracking.carrier}</p>
                    <p className="text-sm"><strong>Number:</strong> {selectedOrder.tracking.tracking_number}</p>
                    <p className="text-sm"><strong>Status:</strong> {selectedOrder.tracking.status_description}</p>
                  </div>
                )}
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedOrder(null)} className="rounded-full">
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Tracking Dialog */}
        <Dialog open={showTrackingDialog} onOpenChange={setShowTrackingDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E]">Add Tracking Information</DialogTitle>
              <DialogDescription>
                Add shipping tracking for order {trackingOrder?.order_number}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Carrier</Label>
                <Select 
                  value={trackingData.carrier} 
                  onValueChange={(value) => setTrackingData(prev => ({ ...prev, carrier: value }))}
                >
                  <SelectTrigger className="rounded-lg" data-testid="carrier-select">
                    <SelectValue placeholder="Select carrier" />
                  </SelectTrigger>
                  <SelectContent>
                    {CARRIERS.map(carrier => (
                      <SelectItem key={carrier.value} value={carrier.value}>{carrier.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Tracking Number</Label>
                <Input
                  value={trackingData.tracking_number}
                  onChange={(e) => setTrackingData(prev => ({ ...prev, tracking_number: e.target.value }))}
                  placeholder="Enter tracking number"
                  className="rounded-lg"
                  data-testid="tracking-number-input"
                />
              </div>
            </div>
            
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setShowTrackingDialog(false)} className="rounded-full">
                Cancel
              </Button>
              <Button 
                onClick={addTracking} 
                disabled={savingTracking}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
                data-testid="save-tracking-btn"
              >
                {savingTracking ? "Saving..." : "Add Tracking"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AdminSidebar>
  );
};

export default AdminOrdersPage;
