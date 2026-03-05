import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useCart } from "../App";
import { 
  CheckCircle, 
  Package, 
  Mail,
  ArrowRight,
  Loader2
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CheckoutSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState("checking");
  const { clearCart } = useCart();
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    }
  }, [sessionId]);

  const pollPaymentStatus = async (attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setPaymentStatus("timeout");
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${BACKEND_URL}/api/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === "paid") {
        setPaymentStatus("paid");
        await clearCart();
        // Fetch order details
        await fetchOrderDetails();
        setLoading(false);
        return;
      } else if (response.data.status === "expired") {
        setPaymentStatus("expired");
        setLoading(false);
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
    } catch (error) {
      console.error("Error checking payment:", error);
      setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
    }
  };

  const fetchOrderDetails = async () => {
    try {
      // We need to get order by session ID, but for now we'll show a generic success
      setOrder({ order_number: "Processing..." });
    } catch (error) {
      console.error("Error fetching order:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-[#2D4A3E] mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-[#2D4A3E] font-['Fraunces']">
            Confirming your payment...
          </h2>
          <p className="text-[#5C6D5E] mt-2">Please wait a moment</p>
        </div>
      </div>
    );
  }

  if (paymentStatus !== "paid") {
    return (
      <div className="min-h-screen pt-24 pb-12 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-20 h-20 bg-[#C45C4A]/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Package className="w-10 h-10 text-[#C45C4A]" />
          </div>
          <h2 className="text-2xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
            Payment Issue
          </h2>
          <p className="text-[#5C6D5E] mb-6">
            {paymentStatus === "expired" 
              ? "Your payment session has expired. Please try again."
              : "We couldn't confirm your payment. Please contact support if you were charged."}
          </p>
          <Link to="/cart">
            <Button className="rounded-full">Return to Cart</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-lg">
          <div className="w-20 h-20 bg-[#6B8F71]/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-[#6B8F71]" />
          </div>
          
          <h1 className="text-3xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
            Thank you for your order!
          </h1>
          
          <p className="text-[#5C6D5E] mb-8">
            Your order has been confirmed and will be shipped soon. 
            We've sent a confirmation email with your order details.
          </p>

          <div className="bg-[#E8DFD5]/30 rounded-2xl p-6 mb-8">
            <div className="flex items-center justify-center gap-3 text-[#2D4A3E]">
              <Mail className="w-5 h-5" />
              <span>Check your email for order confirmation</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/products">
              <Button
                variant="outline"
                className="rounded-full px-8"
                data-testid="continue-shopping"
              >
                Continue Shopping
              </Button>
            </Link>
            <Link to="/account">
              <Button
                className="bg-[#2D4A3E] hover:bg-[#1F342B] text-white rounded-full px-8"
                data-testid="view-orders"
              >
                View Orders
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>

        {/* What's Next */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 text-center">
            <div className="w-12 h-12 bg-[#D4A574]/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-xl">1</span>
            </div>
            <h3 className="font-semibold text-[#2D4A3E] mb-2">Order Processing</h3>
            <p className="text-sm text-[#5C6D5E]">We're preparing your order for shipment</p>
          </div>
          <div className="bg-white rounded-2xl p-6 text-center">
            <div className="w-12 h-12 bg-[#D4A574]/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-xl">2</span>
            </div>
            <h3 className="font-semibold text-[#2D4A3E] mb-2">Shipping</h3>
            <p className="text-sm text-[#5C6D5E]">Your order will ship within 1-3 business days</p>
          </div>
          <div className="bg-white rounded-2xl p-6 text-center">
            <div className="w-12 h-12 bg-[#D4A574]/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-xl">3</span>
            </div>
            <h3 className="font-semibold text-[#2D4A3E] mb-2">Delivery</h3>
            <p className="text-sm text-[#5C6D5E]">Expected delivery in 5-10 business days</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutSuccessPage;
