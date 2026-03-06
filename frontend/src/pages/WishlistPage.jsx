import React from "react";
import { Link } from "react-router-dom";
import { useWishlist, useCart, useAuth } from "../App";
import { toast } from "sonner";
import {
  Heart,
  ShoppingCart,
  Trash2,
  Star,
  ArrowRight,
  Package
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WishlistPage = () => {
  const { wishlist, loading, removeFromWishlist } = useWishlist();
  const { addToCart } = useCart();
  const { token } = useAuth();

  const handleRemove = async (productId, productName) => {
    const success = await removeFromWishlist(productId);
    if (success) {
      toast.success(`Removed "${productName}" from wishlist`);
    } else {
      toast.error("Failed to remove from wishlist");
    }
  };

  const handleAddToCart = async (product) => {
    await addToCart(product.id, 1);
  };

  const handleMoveToCart = async (product) => {
    await addToCart(product.id, 1);
    await removeFromWishlist(product.id);
    toast.success(`Moved "${product.name}" to cart`);
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12 bg-[#FDF8F3]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-10 bg-gray-200 rounded w-1/3 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-2xl p-4">
                  <div className="aspect-square bg-gray-200 rounded-xl mb-4"></div>
                  <div className="h-6 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-12 bg-[#FDF8F3]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#2F3E32] font-['Fraunces']">
              My Wishlist
            </h1>
            <p className="text-[#5C6D5E] mt-1">
              {wishlist.count} {wishlist.count === 1 ? "item" : "items"} saved
            </p>
          </div>
          
          <Link to="/products">
            <Button variant="outline" className="rounded-full" data-testid="continue-shopping-btn">
              Continue Shopping
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>

        {/* Empty State */}
        {wishlist.items.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-[#E8E6DE]">
            <div className="w-20 h-20 mx-auto bg-[#F2F0E9] rounded-full flex items-center justify-center mb-6">
              <Heart className="w-10 h-10 text-[#D4A574]" />
            </div>
            <h2 className="text-2xl font-bold text-[#2F3E32] mb-3 font-['Fraunces']">
              Your wishlist is empty
            </h2>
            <p className="text-[#5C6D5E] mb-6 max-w-md mx-auto">
              Save your favorite products here to find them easily later. Click the heart icon on any product to add it to your wishlist.
            </p>
            <Link to="/products">
              <Button className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full px-8" data-testid="browse-products-btn">
                Browse Products
              </Button>
            </Link>
          </div>
        ) : (
          /* Wishlist Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {wishlist.items.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-2xl border border-[#E8E6DE] overflow-hidden hover:shadow-lg transition-all group"
                data-testid={`wishlist-item-${product.id}`}
              >
                {/* Product Image */}
                <Link to={`/products/${product.slug}`}>
                  <div className="relative aspect-square bg-[#F5F5F5] overflow-hidden">
                    <img
                      src={product.images?.[0] || "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400"}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    
                    {/* Sale Badge */}
                    {product.compare_at_price && product.compare_at_price > product.price && (
                      <span className="absolute top-3 left-3 bg-[#D66D5A] text-white text-xs font-medium px-2 py-1 rounded-full">
                        SALE
                      </span>
                    )}
                    
                    {/* Remove Button */}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleRemove(product.id, product.name);
                      }}
                      className="absolute top-3 right-3 w-10 h-10 bg-white/90 rounded-full flex items-center justify-center hover:bg-red-50 transition-colors"
                      data-testid={`remove-wishlist-${product.id}`}
                    >
                      <Heart className="w-5 h-5 text-[#D66D5A] fill-[#D66D5A]" />
                    </button>
                  </div>
                </Link>

                {/* Product Info */}
                <div className="p-4">
                  {/* Category & Pet Type */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-[#5C6D5E] bg-[#F2F0E9] px-2 py-0.5 rounded-full capitalize">
                      {product.pet_type}
                    </span>
                    <span className="text-xs text-[#5C6D5E]">
                      {product.category}
                    </span>
                  </div>

                  {/* Product Name */}
                  <Link to={`/products/${product.slug}`}>
                    <h3 className="font-semibold text-[#2F3E32] mb-2 line-clamp-2 hover:text-[#6B8F71] transition-colors">
                      {product.name}
                    </h3>
                  </Link>

                  {/* Rating */}
                  {product.rating && (
                    <div className="flex items-center gap-1 mb-3">
                      <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      <span className="text-sm text-[#5C6D5E]">
                        {product.rating} ({product.review_count || 0} reviews)
                      </span>
                    </div>
                  )}

                  {/* Price */}
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-xl font-bold text-[#2D4A3E]">
                      ${product.price?.toFixed(2)}
                    </span>
                    {product.compare_at_price && product.compare_at_price > product.price && (
                      <span className="text-sm text-[#9CA3AF] line-through">
                        ${product.compare_at_price?.toFixed(2)}
                      </span>
                    )}
                  </div>

                  {/* Stock Status */}
                  <div className="flex items-center gap-2 mb-4">
                    {product.in_stock ? (
                      <span className="text-sm text-green-600 flex items-center gap-1">
                        <Package className="w-4 h-4" />
                        In Stock
                      </span>
                    ) : (
                      <span className="text-sm text-red-600">Out of Stock</span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleMoveToCart(product)}
                      disabled={!product.in_stock}
                      className="flex-1 bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
                      data-testid={`move-to-cart-${product.id}`}
                    >
                      <ShoppingCart className="w-4 h-4 mr-2" />
                      Move to Cart
                    </Button>
                    <Button
                      onClick={() => handleRemove(product.id, product.name)}
                      variant="outline"
                      className="rounded-xl px-3"
                      data-testid={`delete-wishlist-${product.id}`}
                    >
                      <Trash2 className="w-4 h-4 text-[#D66D5A]" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Continue Shopping Section */}
        {wishlist.items.length > 0 && (
          <div className="mt-12 text-center">
            <p className="text-[#5C6D5E] mb-4">Looking for more?</p>
            <Link to="/products">
              <Button variant="outline" className="rounded-full px-8" data-testid="discover-more-btn">
                Discover More Products
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default WishlistPage;
