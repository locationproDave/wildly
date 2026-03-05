import React from "react";
import { Link } from "react-router-dom";
import { useCart } from "../App";
import { 
  X, 
  Minus, 
  Plus, 
  ShoppingBag,
  Trash2
} from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";

const CartDrawer = ({ isOpen, onClose }) => {
  const { cart, updateQuantity, removeFromCart } = useCart();

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="cart-overlay animate-fade-in" 
        onClick={onClose}
        data-testid="cart-overlay"
      />
      
      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full max-w-md bg-[#FDF8F3] shadow-2xl z-50 animate-slide-in-right flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#E8DFD5]">
          <h2 className="text-xl font-bold text-[#2D4A3E] font-['Fraunces']">
            Your Cart ({cart.item_count || 0})
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#E8DFD5] rounded-full transition-colors"
            data-testid="close-cart"
          >
            <X className="w-5 h-5 text-[#5C6D5E]" />
          </button>
        </div>

        {/* Cart Items */}
        {cart.items && cart.items.length > 0 ? (
          <>
            <ScrollArea className="flex-1 p-6">
              <div className="space-y-4">
                {cart.items.map((item) => (
                  <div
                    key={item.product_id}
                    className="flex gap-4 bg-white p-4 rounded-xl"
                    data-testid={`cart-item-${item.product_id}`}
                  >
                    <img
                      src={item.product?.images?.[0] || "https://via.placeholder.com/100"}
                      alt={item.product?.name}
                      className="w-20 h-20 object-cover rounded-lg"
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-[#2D4A3E] text-sm line-clamp-2">
                        {item.product?.name}
                      </h3>
                      <p className="text-[#D4A574] font-semibold mt-1">
                        ${item.product?.price?.toFixed(2)}
                      </p>
                      
                      {/* Quantity Controls */}
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center border border-[#E8DFD5] rounded-full">
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                            className="p-1.5 hover:bg-[#E8DFD5] rounded-l-full"
                            data-testid={`decrease-${item.product_id}`}
                          >
                            <Minus className="w-3 h-3 text-[#2D4A3E]" />
                          </button>
                          <span className="px-3 text-sm font-semibold text-[#2D4A3E]">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                            className="p-1.5 hover:bg-[#E8DFD5] rounded-r-full"
                            data-testid={`increase-${item.product_id}`}
                          >
                            <Plus className="w-3 h-3 text-[#2D4A3E]" />
                          </button>
                        </div>
                        <button
                          onClick={() => removeFromCart(item.product_id)}
                          className="p-2 text-[#C45C4A] hover:bg-[#C45C4A]/10 rounded-full"
                          data-testid={`remove-${item.product_id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Footer */}
            <div className="p-6 border-t border-[#E8DFD5] bg-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#5C6D5E]">Subtotal</span>
                <span className="font-semibold text-[#2D4A3E]">
                  ${cart.subtotal?.toFixed(2)}
                </span>
              </div>
              {cart.subtotal < 50 && (
                <p className="text-sm text-[#5C6D5E] mb-4">
                  Add ${(50 - cart.subtotal).toFixed(2)} more for free shipping!
                </p>
              )}
              {cart.subtotal >= 50 && (
                <p className="text-sm text-[#6B8F71] mb-4">
                  🎉 You qualify for free shipping!
                </p>
              )}
              <Link to="/cart" onClick={onClose}>
                <Button
                  className="w-full bg-[#2D4A3E] hover:bg-[#1F342B] text-white py-6 rounded-full font-semibold"
                  data-testid="view-cart-btn"
                >
                  View Cart & Checkout
                </Button>
              </Link>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div className="w-20 h-20 bg-[#E8DFD5] rounded-full flex items-center justify-center mb-4">
              <ShoppingBag className="w-10 h-10 text-[#5C6D5E]" />
            </div>
            <h3 className="text-xl font-semibold text-[#2D4A3E] mb-2 font-['Fraunces']">
              Your cart is empty
            </h3>
            <p className="text-[#5C6D5E] mb-6">
              Start shopping to add items to your cart
            </p>
            <Link to="/products" onClick={onClose}>
              <Button className="rounded-full" data-testid="start-shopping">
                Start Shopping
              </Button>
            </Link>
          </div>
        )}
      </div>
    </>
  );
};

export default CartDrawer;
