import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../App";
import { 
  Package, 
  Truck, 
  MapPin, 
  CheckCircle,
  Clock,
  ExternalLink,
  AlertCircle
} from "lucide-react";
import { Button } from "./ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const statusSteps = [
  { key: "pending", label: "Order Placed", icon: Package },
  { key: "processing", label: "Processing", icon: Clock },
  { key: "shipped", label: "Shipped", icon: Truck },
  { key: "out_for_delivery", label: "Out for Delivery", icon: MapPin },
  { key: "delivered", label: "Delivered", icon: CheckCircle }
];

const getStatusIndex = (status) => {
  const statusMap = {
    pending: 0,
    processing: 1,
    shipped: 2,
    in_transit: 2,
    out_for_delivery: 3,
    delivered: 4
  };
  return statusMap[status] || 0;
};

const OrderTracking = ({ orderId, orderStatus }) => {
  const { token } = useAuth();
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTracking();
  }, [orderId]);

  const fetchTracking = async () => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/orders/${orderId}/tracking`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTracking(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load tracking");
    } finally {
      setLoading(false);
    }
  };

  const currentStep = tracking?.has_tracking 
    ? getStatusIndex(tracking.status) 
    : getStatusIndex(orderStatus);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-24 bg-gray-100 rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm" data-testid="order-tracking">
      <h3 className="font-semibold text-[#2D4A3E] mb-6">Order Tracking</h3>

      {/* Progress Steps */}
      <div className="relative mb-8">
        <div className="flex justify-between">
          {statusSteps.map((step, index) => {
            const StepIcon = step.icon;
            const isCompleted = index <= currentStep;
            const isCurrent = index === currentStep;
            
            return (
              <div key={step.key} className="flex flex-col items-center relative z-10">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  isCompleted 
                    ? "bg-[#6B8F71] text-white" 
                    : "bg-[#E8DFD5] text-[#5C6D5E]"
                } ${isCurrent ? "ring-4 ring-[#6B8F71]/20" : ""}`}>
                  <StepIcon className="w-5 h-5" />
                </div>
                <p className={`text-xs mt-2 text-center ${
                  isCompleted ? "text-[#2D4A3E] font-medium" : "text-[#5C6D5E]"
                }`}>
                  {step.label}
                </p>
              </div>
            );
          })}
        </div>
        
        {/* Progress Bar */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-[#E8DFD5] -z-0">
          <div 
            className="h-full bg-[#6B8F71] transition-all duration-500"
            style={{ width: `${(currentStep / (statusSteps.length - 1)) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Tracking Details */}
      {tracking?.has_tracking ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-[#FDF8F3] rounded-xl">
            <div>
              <p className="text-sm text-[#5C6D5E]">Carrier</p>
              <p className="font-semibold text-[#2D4A3E]">{tracking.carrier}</p>
            </div>
            <div>
              <p className="text-sm text-[#5C6D5E]">Tracking Number</p>
              <p className="font-mono text-[#2D4A3E]">{tracking.tracking_number}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(tracking.tracking_url, '_blank')}
              className="rounded-full"
              data-testid="track-package-btn"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Track
            </Button>
          </div>

          {tracking.status_description && (
            <div className="p-4 bg-[#6B8F71]/10 rounded-xl">
              <p className="font-medium text-[#2D4A3E]">{tracking.status_description}</p>
              {tracking.last_location && (
                <p className="text-sm text-[#5C6D5E] flex items-center gap-1 mt-1">
                  <MapPin className="w-4 h-4" />
                  {tracking.last_location}
                </p>
              )}
              {tracking.estimated_delivery && (
                <p className="text-sm text-[#5C6D5E] mt-1">
                  Estimated delivery: {new Date(tracking.estimated_delivery).toLocaleDateString()}
                </p>
              )}
            </div>
          )}

          {/* Tracking Events */}
          {tracking.events && tracking.events.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-[#2D4A3E] mb-3">Tracking History</h4>
              <div className="space-y-3">
                {tracking.events.slice().reverse().map((event, idx) => (
                  <div key={idx} className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-[#6B8F71] mt-1.5 shrink-0"></div>
                    <div>
                      <p className="text-[#2D4A3E]">{event.description}</p>
                      <p className="text-[#5C6D5E]">
                        {event.location && `${event.location} • `}
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center p-6 bg-[#FDF8F3] rounded-xl">
          <AlertCircle className="w-10 h-10 text-[#D4A574] mx-auto mb-3" />
          <p className="text-[#5C6D5E]">
            {tracking?.message || "Tracking information will be available once your order ships."}
          </p>
          <p className="text-sm text-[#5C6D5E] mt-2">
            You'll receive an email with tracking details.
          </p>
        </div>
      )}
    </div>
  );
};

export default OrderTracking;
