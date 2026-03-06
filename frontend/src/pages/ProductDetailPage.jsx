import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { useCart, useWishlist, useAuth } from "../App";
import { toast } from "sonner";
import { 
  Star, 
  Dog, 
  Cat, 
  Truck, 
  RotateCcw, 
  Shield,
  Minus,
  Plus,
  ChevronLeft,
  Check,
  Bird,
  Fish,
  Rabbit,
  Squirrel,
  Heart
} from "lucide-react";
import { Button } from "../components/ui/button";
import ProductReviews from "../components/ProductReviews";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ProductDetailPage = () => {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const { addToCart } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const { user } = useAuth();

  useEffect(() => {
    fetchProduct();
  }, [slug]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/products/${slug}`);
      setProduct(response.data);
    } catch (error) {
      console.error("Error fetching product:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    addToCart(product.id, quantity);
  };

  const handleWishlist = async () => {
    if (!user) {
      toast.error("Please sign in to save to wishlist");
      return;
    }
    const success = await toggleWishlist(product.id);
    if (success) {
      const inWishlist = isInWishlist(product.id);
      toast.success(inWishlist ? "Removed from wishlist" : "Added to wishlist");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="bg-gray-200 rounded-3xl h-[500px] animate-pulse"></div>
            <div className="space-y-4">
              <div className="bg-gray-200 h-8 rounded w-3/4 animate-pulse"></div>
              <div className="bg-gray-200 h-4 rounded w-1/2 animate-pulse"></div>
              <div className="bg-gray-200 h-32 rounded animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen pt-24 pb-12 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
            Product not found
          </h2>
          <Link to="/products">
            <Button className="rounded-full">Back to Products</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <Link 
          to="/products" 
          className="inline-flex items-center text-[#5C6D5E] hover:text-[#2D4A3E] mb-4 text-sm"
          data-testid="back-to-products"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Products
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Product Image */}
          <div className="relative">
            <div className="bg-white rounded-3xl overflow-hidden shadow-lg">
              <img
                src={product.images?.[0] || "https://via.placeholder.com/600"}
                alt={product.name}
                className="w-full h-[500px] object-cover"
              />
            </div>
            {product.compare_at_price && (
              <span className="absolute top-6 left-6 bg-[#C45C4A] text-white px-4 py-2 rounded-full font-semibold">
                {Math.round((1 - product.price / product.compare_at_price) * 100)}% OFF
              </span>
            )}
          </div>

          {/* Product Info */}
          <div>
            {/* Pet Type Badge */}
            <div className="flex gap-2 mb-4">
              {(product.pet_type === "dog" || product.pet_type === "both") && (
                <span className="inline-flex items-center gap-1 bg-[#E8DFD5] text-[#2D4A3E] px-3 py-1 rounded-full text-sm">
                  <Dog className="w-4 h-4" />
                  For Dogs
                </span>
              )}
              {(product.pet_type === "cat" || product.pet_type === "both") && (
                <span className="inline-flex items-center gap-1 bg-[#E8DFD5] text-[#2D4A3E] px-3 py-1 rounded-full text-sm">
                  <Cat className="w-4 h-4" />
                  For Cats
                </span>
              )}
              {product.pet_type === "reptile" && (
                <span className="inline-flex items-center gap-1 bg-[#9B8B7A]/20 text-[#9B8B7A] px-3 py-1 rounded-full text-sm">
                  <Egg className="w-4 h-4" />
                  For Reptiles
                </span>
              )}
            </div>

            <h1 className="text-3xl md:text-4xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
              {product.name}
            </h1>

            {/* Rating */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-5 h-5 ${i < Math.floor(product.rating) ? 'fill-[#D4A574] text-[#D4A574]' : 'text-[#E8DFD5]'}`}
                  />
                ))}
              </div>
              <span className="text-[#5C6D5E]">
                {product.rating} ({product.review_count} reviews)
              </span>
            </div>

            {/* Price */}
            <div className="flex items-center gap-3 mb-6">
              <span className="text-3xl font-bold text-[#2D4A3E]">
                ${product.price.toFixed(2)}
              </span>
              {product.compare_at_price && (
                <span className="text-xl text-[#5C6D5E] line-through">
                  ${product.compare_at_price.toFixed(2)}
                </span>
              )}
            </div>

            {/* Description */}
            <p className="text-[#5C6D5E] leading-relaxed mb-8">
              {product.description}
            </p>

            {/* Features */}
            {product.features && product.features.length > 0 && (
              <div className="mb-8">
                <h3 className="font-semibold text-[#2D4A3E] mb-3">Key Features</h3>
                <ul className="space-y-2">
                  {product.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-[#5C6D5E]">
                      <Check className="w-5 h-5 text-[#6B8F71]" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quantity & Add to Cart */}
            <div className="flex items-center gap-4 mb-8">
              <div className="flex items-center border border-[#E8DFD5] rounded-full">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="p-3 hover:bg-[#E8DFD5] rounded-l-full transition-colors"
                  data-testid="decrease-qty"
                >
                  <Minus className="w-4 h-4 text-[#2D4A3E]" />
                </button>
                <span className="px-6 font-semibold text-[#2D4A3E]" data-testid="quantity">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="p-3 hover:bg-[#E8DFD5] rounded-r-full transition-colors"
                  data-testid="increase-qty"
                >
                  <Plus className="w-4 h-4 text-[#2D4A3E]" />
                </button>
              </div>
              <Button
                onClick={handleAddToCart}
                className="flex-1 bg-[#2D4A3E] hover:bg-[#1F342B] text-white py-6 rounded-full font-semibold text-lg"
                data-testid="add-to-cart-btn"
              >
                Add to Cart — ${(product.price * quantity).toFixed(2)}
              </Button>
              <Button
                onClick={handleWishlist}
                variant="outline"
                className={`p-4 rounded-full border-[#E8DFD5] ${isInWishlist(product.id) ? 'bg-red-50' : ''}`}
                data-testid="wishlist-btn"
              >
                <Heart 
                  className={`w-6 h-6 ${isInWishlist(product.id) ? 'fill-[#D66D5A] text-[#D66D5A]' : 'text-[#5C6D5E]'}`} 
                />
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-[#E8DFD5]/30 rounded-2xl">
              <div className="text-center">
                <Truck className="w-6 h-6 mx-auto mb-2 text-[#2D4A3E]" />
                <p className="text-xs text-[#5C6D5E]">Free shipping over $50</p>
              </div>
              <div className="text-center">
                <RotateCcw className="w-6 h-6 mx-auto mb-2 text-[#2D4A3E]" />
                <p className="text-xs text-[#5C6D5E]">30-day returns</p>
              </div>
              <div className="text-center">
                <Shield className="w-6 h-6 mx-auto mb-2 text-[#2D4A3E]" />
                <p className="text-xs text-[#5C6D5E]">Secure checkout</p>
              </div>
            </div>

            {/* Additional Info */}
            {(product.dimensions || product.ingredients) && (
              <div className="mt-8 space-y-4">
                {product.dimensions && (
                  <div>
                    <h3 className="font-semibold text-[#2D4A3E] mb-1">Dimensions</h3>
                    <p className="text-[#5C6D5E]">{product.dimensions}</p>
                  </div>
                )}
                {product.ingredients && (
                  <div>
                    <h3 className="font-semibold text-[#2D4A3E] mb-1">Ingredients</h3>
                    <p className="text-[#5C6D5E]">{product.ingredients}</p>
                  </div>
                )}
              </div>
            )}

            {/* Vet Note */}
            <div className="mt-8 p-4 bg-[#6B8F71]/10 rounded-xl border border-[#6B8F71]/20">
              <p className="text-sm text-[#5C6D5E]">
                <strong className="text-[#2D4A3E]">Veterinarian Note:</strong> As always, we recommend consulting your veterinarian before introducing any new wellness product into your pet's routine, especially if your pet has existing health conditions or is on medication.
              </p>
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <ProductReviews productSlug={slug} />
      </div>
    </div>
  );
};

export default ProductDetailPage;
