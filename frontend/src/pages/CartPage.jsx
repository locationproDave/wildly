import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useCart, useAuth } from "../App";
import { toast } from "sonner";
import { 
  Minus, 
  Plus, 
  Trash2, 
  ShoppingBag,
  ChevronLeft,
  Truck,
  Lock
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CartPage = () => {
  const { cart, sessionId, updateQuantity, removeFromCart } = useCart();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState(user?.email || "");

  const subtotal = cart.subtotal || 0;
  const shipping = subtotal >= 50 ? 0 : 5.99;
  const tax = subtotal * 0.08;
  const total = subtotal + shipping + tax;

  const handleCheckout = async () => {
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/checkout`,
        {
          cart_session_id: sessionId,
          email: email,
          origin_url: window.location.origin
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
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link 
          to="/products" 
          className="inline-flex items-center text-[#5C6D5E] hover:text-[#2D4A3E] mb-8"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Continue Shopping
        </Link>

        <h1 className="text-3xl font-bold text-[#2D4A3E] mb-8 font-['Fraunces']">
          Shopping Cart
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
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

              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-[#5C6D5E]">
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
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

              <Button
                onClick={handleCheckout}
                disabled={loading}
                className="w-full bg-[#2D4A3E] hover:bg-[#1F342B] text-white py-6 rounded-full font-semibold"
                data-testid="checkout-btn"
              >
                {loading ? (
                  "Processing..."
                ) : (
                  <>
                    <Lock className="w-4 h-4 mr-2" />
                    Secure Checkout
                  </>
                )}
              </Button>

              <p className="text-xs text-[#5C6D5E] text-center mt-4">
                Secure payment powered by Stripe
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
