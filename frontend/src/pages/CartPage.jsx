import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { useCart, useAuth } from "../App";
import { toast } from "sonner";
import { 
  Minus, 
  Plus, 
  Trash2, 
  ShoppingBag,
  ChevronLeft,
  Truck,
  Lock,
  Tag,
  X,
  CreditCard,
  CheckCircle,
  RefreshCw,
  Calendar
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const PAYPAL_CLIENT_ID = process.env.REACT_APP_PAYPAL_CLIENT_ID || "sb"; // sandbox default

const CartPage = () => {
  const { cart, sessionId, updateQuantity, removeFromCart, refreshCart } = useCart();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState(user?.email || "");
  const [promoCode, setPromoCode] = useState("");
  const [promoLoading, setPromoLoading] = useState(false);
  const [appliedPromo, setAppliedPromo] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState("stripe"); // stripe or paypal
  const [isSubscription, setIsSubscription] = useState(false);

  const SUBSCRIPTION_DISCOUNT = 10; // 10% off for subscribers
  const subtotal = cart.subtotal || 0;
  const subscriptionDiscount = isSubscription ? subtotal * (SUBSCRIPTION_DISCOUNT / 100) : 0;
  const shipping = subtotal >= 50 ? 0 : 5.99;
  const promoDiscount = appliedPromo?.discount_amount || 0;
  const discountedSubtotal = Math.max(0, subtotal - promoDiscount - subscriptionDiscount);
  const tax = discountedSubtotal * 0.08;
  const total = discountedSubtotal + shipping + tax;

  const applyPromoCode = async () => {
    if (!promoCode.trim()) {
      toast.error("Please enter a promo code");
      return;
    }

    setPromoLoading(true);
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/promotions/validate/${promoCode.trim()}?subtotal=${subtotal}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      
      setAppliedPromo(response.data);
      toast.success(`Promo code applied! You save $${response.data.discount_amount.toFixed(2)}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid promo code");
      setAppliedPromo(null);
    } finally {
      setPromoLoading(false);
    }
  };

  const removePromoCode = () => {
    setAppliedPromo(null);
    setPromoCode("");
    toast.info("Promo code removed");
  };

  const handleStripeCheckout = async () => {
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    setLoading(true);
    try {
      const endpoint = isSubscription ? `${BACKEND_URL}/api/checkout/subscription` : `${BACKEND_URL}/api/checkout`;
      const response = await axios.post(
        endpoint,
        {
          cart_session_id: sessionId,
          email: email,
          origin_url: window.location.origin,
          promo_code: appliedPromo?.promotion?.code || null
        },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      );

      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create checkout");
    } finally {
      setLoading(false);
    }
  };

  const createPayPalOrder = async () => {
    if (!email) {
      toast.error("Please enter your email address");
      throw new Error("Email required");
    }

    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/paypal/create-order`,
        {
          cart_session_id: sessionId,
          email: email,
          promo_code: appliedPromo?.promotion?.code || null
        },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      );
      return response.data.order_id;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create PayPal order");
      throw error;
    }
  };

  const onPayPalApprove = async (data) => {
    try {
      setLoading(true);
      const response = await axios.post(
        `${BACKEND_URL}/api/paypal/capture-order/${data.orderID}`,
        {},
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      
      toast.success("Payment successful!");
      refreshCart();
      navigate(`/order-confirmation?order_id=${response.data.order_id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment capture failed");
    } finally {
      setLoading(false);
    }
  };

  if (!cart.items || cart.items.length === 0) {
    return (
      <div className="min-h-screen pt-24 pb-12 flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-[#E8DFD5] rounded-full flex items-center justify-center mx-auto mb-6">
            <ShoppingBag className="w-12 h-12 text-[#5C6D5E]" />
          </div>
          <h2 className="text-2xl font-bold text-[#2D4A3E] mb-2 font-['Fraunces']">
            Your cart is empty
          </h2>
          <p className="text-[#5C6D5E] mb-6">
            Looks like you haven't added anything to your cart yet
          </p>
          <Link to="/products">
            <Button className="rounded-full" data-testid="continue-shopping">
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link 
          to="/products" 
          className="inline-flex items-center text-[#5C6D5E] hover:text-[#2D4A3E] mb-4 text-sm"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Continue Shopping
        </Link>

        <h1 className="text-2xl font-bold text-[#2D4A3E] mb-5 font-['Fraunces']">
          Shopping Cart
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {cart.items.map((item) => (
              <div
                key={item.product_id}
                className="flex gap-4 bg-white p-6 rounded-2xl shadow-sm"
                data-testid={`cart-item-${item.product_id}`}
              >
                <img
                  src={item.product?.images?.[0] || "https://via.placeholder.com/150"}
                  alt={item.product?.name}
                  className="w-24 h-24 object-cover rounded-xl"
                />
                <div className="flex-1">
                  <div className="flex justify-between">
                    <div>
                      <Link to={`/products/${item.product?.slug}`}>
                        <h3 className="font-semibold text-[#2D4A3E] hover:text-[#D4A574] transition-colors">
                          {item.product?.name}
                        </h3>
                      </Link>
                      <p className="text-sm text-[#5C6D5E] mt-1">
                        ${item.product?.price?.toFixed(2)} each
                      </p>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.product_id)}
                      className="p-2 text-[#C45C4A] hover:bg-[#C45C4A]/10 rounded-full h-fit"
                      data-testid={`remove-${item.product_id}`}
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                  
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center border border-[#E8DFD5] rounded-full">
                      <button
                        onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                        className="p-2 hover:bg-[#E8DFD5] rounded-l-full"
                      >
                        <Minus className="w-4 h-4 text-[#2D4A3E]" />
                      </button>
                      <span className="px-4 font-semibold text-[#2D4A3E]">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                        className="p-2 hover:bg-[#E8DFD5] rounded-r-full"
                      >
                        <Plus className="w-4 h-4 text-[#2D4A3E]" />
                      </button>
                    </div>
                    <p className="font-semibold text-[#2D4A3E]">
                      ${(item.product?.price * item.quantity).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-2xl shadow-sm sticky top-24">
              <h2 className="text-xl font-bold text-[#2D4A3E] mb-6 font-['Fraunces']">
                Order Summary
              </h2>

              {/* Promo Code Input */}
              <div className="mb-6">
                <Label className="text-[#2D4A3E] flex items-center gap-2 mb-2">
                  <Tag className="w-4 h-4" />
                  Promo Code
                </Label>
                {appliedPromo ? (
                  <div className="flex items-center justify-between bg-[#6B8F71]/10 p-3 rounded-xl">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-[#6B8F71]" />
                      <div>
                        <p className="font-semibold text-[#2D4A3E]">{appliedPromo.promotion.code}</p>
                        <p className="text-xs text-[#5C6D5E]">-${appliedPromo.discount_amount.toFixed(2)} off</p>
                      </div>
                    </div>
                    <button
                      onClick={removePromoCode}
                      className="p-1 hover:bg-[#2D4A3E]/10 rounded-full"
                      data-testid="remove-promo"
                    >
                      <X className="w-4 h-4 text-[#5C6D5E]" />
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <Input
                      value={promoCode}
                      onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                      placeholder="Enter code"
                      className="rounded-xl flex-1"
                      data-testid="promo-input"
                    />
                    <Button
                      onClick={applyPromoCode}
                      disabled={promoLoading}
                      variant="outline"
                      className="rounded-xl"
                      data-testid="apply-promo-btn"
                    >
                      {promoLoading ? "..." : "Apply"}
                    </Button>
                  </div>
                )}
                <p className="text-xs text-[#5C6D5E] mt-2">
                  Try: WELCOME15, PAWS10, SPRING25
                </p>
              </div>

              {/* Monthly Subscription Option */}
              <div className="mb-6">
                <button
                  onClick={() => setIsSubscription(!isSubscription)}
                  className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                    isSubscription 
                      ? "border-[#6B8F71] bg-[#6B8F71]/10" 
                      : "border-[#E8DFD5] hover:border-[#D4A574]"
                  }`}
                  data-testid="subscription-toggle"
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 ${
                      isSubscription ? "border-[#6B8F71] bg-[#6B8F71]" : "border-[#5C6D5E]"
                    }`}>
                      {isSubscription && <CheckCircle className="w-3 h-3 text-white" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <RefreshCw className="w-4 h-4 text-[#6B8F71]" />
                        <span className="font-semibold text-[#2D4A3E]">Subscribe & Save 10%</span>
                      </div>
                      <p className="text-xs text-[#5C6D5E] mt-1">
                        Get this order delivered monthly and save on every shipment. Cancel anytime.
                      </p>
                      {isSubscription && (
                        <div className="flex items-center gap-2 mt-2 text-xs text-[#6B8F71]">
                          <Calendar className="w-3 h-3" />
                          <span>Next delivery in 30 days</span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-[#5C6D5E]">
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                {isSubscription && (
                  <div className="flex justify-between text-[#6B8F71]">
                    <span className="flex items-center gap-1">
                      <RefreshCw className="w-3 h-3" />
                      Subscription Savings
                    </span>
                    <span>-${subscriptionDiscount.toFixed(2)}</span>
                  </div>
                )}
                {appliedPromo && (
                  <div className="flex justify-between text-[#6B8F71]">
                    <span>Promo Discount</span>
                    <span>-${promoDiscount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-[#5C6D5E]">
                  <span className="flex items-center gap-1">
                    <Truck className="w-4 h-4" />
                    Shipping
                  </span>
                  <span>{shipping === 0 ? "Free" : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className="flex justify-between text-[#5C6D5E]">
                  <span>Tax</span>
                  <span>${tax.toFixed(2)}</span>
                </div>
                <div className="border-t border-[#E8DFD5] pt-3">
                  <div className="flex justify-between font-bold text-[#2D4A3E] text-lg">
                    <span>Total</span>
                    <span>${total.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {subtotal < 50 && (
                <div className="bg-[#D4A574]/10 p-3 rounded-xl mb-6">
                  <p className="text-sm text-[#5C6D5E]">
                    Add <strong>${(50 - subtotal).toFixed(2)}</strong> more for free shipping!
                  </p>
                </div>
              )}

              {/* Email Input */}
              <div className="mb-6">
                <Label htmlFor="email" className="text-[#2D4A3E]">Email for order updates</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="mt-2 rounded-xl"
                  data-testid="checkout-email"
                />
              </div>

              {/* Payment Method Selection */}
              <div className="mb-6">
                <Label className="text-[#2D4A3E] mb-3 block">Payment Method</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setPaymentMethod("stripe")}
                    className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                      paymentMethod === "stripe" 
                        ? "border-[#2D4A3E] bg-[#2D4A3E]/5" 
                        : "border-[#E8DFD5] hover:border-[#D4A574]"
                    }`}
                    data-testid="payment-stripe"
                  >
                    <CreditCard className="w-6 h-6 text-[#2D4A3E]" />
                    <span className="text-sm font-medium text-[#2D4A3E]">Card</span>
                  </button>
                  <button
                    onClick={() => setPaymentMethod("paypal")}
                    className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                      paymentMethod === "paypal" 
                        ? "border-[#0070BA] bg-[#0070BA]/5" 
                        : "border-[#E8DFD5] hover:border-[#0070BA]"
                    }`}
                    data-testid="payment-paypal"
                  >
                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="#0070BA">
                      <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c1.025 4.54-1.563 6.818-5.818 6.818H12.1l-1.35 8.559h3.727a.64.64 0 0 0 .632-.54l.026-.165.49-3.103.031-.169a.64.64 0 0 1 .632-.54h.398c2.58 0 4.597-.849 5.187-3.303.25-1.037.17-1.903-.31-2.516-.145-.183-.326-.343-.541-.5z"/>
                    </svg>
                    <span className="text-sm font-medium text-[#0070BA]">PayPal</span>
                  </button>
                </div>
              </div>

              {/* Checkout Buttons */}
              {paymentMethod === "stripe" ? (
                <Button
                  onClick={handleStripeCheckout}
                  disabled={loading || !email}
                  className="w-full bg-[#2D4A3E] hover:bg-[#1F342B] text-white py-6 rounded-full font-semibold"
                  data-testid="checkout-btn"
                >
                  {loading ? (
                    "Processing..."
                  ) : (
                    <>
                      <Lock className="w-4 h-4 mr-2" />
                      Pay ${total.toFixed(2)} with Card
                    </>
                  )}
                </Button>
              ) : (
                <PayPalScriptProvider options={{ 
                  clientId: PAYPAL_CLIENT_ID,
                  currency: "USD"
                }}>
                  <PayPalButtons
                    style={{ 
                      layout: "vertical",
                      shape: "pill",
                      label: "pay"
                    }}
                    disabled={!email || loading}
                    createOrder={createPayPalOrder}
                    onApprove={onPayPalApprove}
                    onError={(err) => {
                      console.error("PayPal Error:", err);
                      toast.error("PayPal payment failed. Please try again.");
                    }}
                  />
                </PayPalScriptProvider>
              )}

              <p className="text-xs text-[#5C6D5E] text-center mt-4">
                {paymentMethod === "stripe" 
                  ? "Secure payment powered by Stripe" 
                  : "Secure payment powered by PayPal"}
              </p>

              {/* Refer & Earn */}
              <div className="mt-6 pt-6 border-t border-[#E8DFD5]">
                <Link 
                  to="/referral"
                  className="flex items-center justify-center gap-2 p-3 bg-[#D4A574]/10 hover:bg-[#D4A574]/20 rounded-xl transition-colors"
                >
                  <span className="text-lg">🎁</span>
                  <div className="text-center">
                    <p className="font-semibold text-[#2D4A3E] text-sm">Refer & Earn $10</p>
                    <p className="text-xs text-[#5C6D5E]">Share with friends, get rewards!</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
