import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useCart } from "../App";
import { 
  ArrowRight, 
  Star, 
  Truck, 
  Shield, 
  Heart,
  Sparkles,
  Pill,
  Bone,
  Scissors,
  Package,
  Bed,
  Gift,
  Award,
  TrendingUp,
  Percent,
  X,
  RefreshCw,
  ShoppingBag
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const HomePage = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [bestsellers, setBestsellers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPromoBanner, setShowPromoBanner] = useState(true);
  const { addToCart } = useCart();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const [featuredRes, bestsellersRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/products/featured`),
        axios.get(`${BACKEND_URL}/api/products/bestsellers`)
      ]);
      setFeaturedProducts(featuredRes.data);
      setBestsellers(bestsellersRes.data);
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Truck className="w-6 h-6" />,
      title: "Free Shipping Over $50",
      description: "Fast delivery from US warehouses"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "30-Day Returns",
      description: "Not satisfied? Full refund, no questions"
    },
    {
      icon: <Heart className="w-6 h-6" />,
      title: "Vet-Informed",
      description: "Science-backed, never overpromising"
    }
  ];

  const categories = [
    { name: "Supplements", slug: "Supplements", icon: Pill, color: "#6B8F71" },
    { name: "Treats", slug: "Treats", icon: Bone, color: "#D4A574" },
    { name: "Toys", slug: "Toys", icon: Gift, color: "#7CA5B8" },
    { name: "Grooming", slug: "Grooming", icon: Scissors, color: "#9B8B7A" },
    { name: "Food", slug: "Food", icon: Package, color: "#D66D5A" },
    { name: "Beds", slug: "Beds", icon: Bed, color: "#768A75" },
    { name: "Accessories", slug: "Accessories", icon: ShoppingBag, color: "#E8B05C" },
    { name: "Health", slug: "Health", icon: Heart, color: "#C45C4A" }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-b from-[#E8DFD5] to-[#FDF8F3] overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 sm:pt-24 pb-12 sm:pb-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Left Content */}
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center gap-2 bg-[#6B8F71]/20 text-[#6B8F71] px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium mb-4 sm:mb-6">
                <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />
                <span>Premium Pet Wellness</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-tight text-[#2D4A3E] mb-4 sm:mb-6 font-['Fraunces']">
                Happy pets <span className="text-[#E8C9A0]">start</span>
                <br />
                <span className="text-[#E8C9A0]">with</span> <span className="text-[#D4A574]">better care.</span>
              </h1>
              
              <p className="text-base sm:text-lg md:text-xl leading-relaxed text-[#5C6D5E] mb-6 sm:mb-8 max-w-lg">
                Nature-inspired, science-backed wellness for the animals who fill your life with joy.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Link to="/products">
                  <Button 
                    className="bg-[#2D4A3E] hover:bg-[#1F342B] text-white px-8 sm:px-10 py-5 sm:py-6 rounded-full font-semibold text-base sm:text-lg inline-flex items-center gap-2 w-full sm:w-auto justify-center"
                    data-testid="hero-shop-btn"
                  >
                    Shop Now
                    <ArrowRight className="w-5 h-5" />
                  </Button>
                </Link>
              </div>
            </div>
            
            {/* Right Image */}
            <div className="relative animate-fade-in stagger-2 hidden lg:block">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800"
                  alt="Happy relaxed dog"
                  className="w-full h-[400px] lg:h-[500px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#2D4A3E]/20 to-transparent"></div>
              </div>
              
            </div>
          </div>
        </div>
      </section>

      {/* Subscribe & Save Banner - Light Sage Green */}
      <section className="bg-[#7A9A7E] py-8 sm:py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-white">
              <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-white/15 flex items-center justify-center flex-shrink-0">
                <RefreshCw className="w-6 h-6 sm:w-7 sm:h-7" />
              </div>
              <div>
                <h3 className="text-xl sm:text-2xl font-bold font-['Fraunces']">Subscribe & Save 10%</h3>
                <p className="text-white/80 text-sm sm:text-base">
                  Never run out of what keeps your pet healthy.
                </p>
                <p className="text-white/80 text-sm sm:text-base">
                  Wellness essentials delivered to your door every month.
                </p>
              </div>
            </div>
            <Link to="/products">
              <Button 
                className="bg-white text-[#2D4A3E] hover:bg-gray-100 rounded-lg px-8 py-3 font-semibold text-base shadow-md"
                data-testid="subscribe-cta"
              >
                Shop Now
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Trust Badges - Darker Green */}
      <section className="bg-[#4A6B4F] py-8 sm:py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            {features.map((feature, index) => (
              <div key={index} className={`flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-white text-center sm:text-left ${index === 2 ? 'sm:flex-row-reverse sm:text-right' : ''}`}>
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                  {feature.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-xs sm:text-base font-['Fraunces']">{feature.title}</h3>
                  <p className="text-white/70 text-xs hidden sm:block">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
              Shop by Category
            </h2>
            <p className="text-[#5C6D5E] max-w-xl mx-auto">
              Find the perfect wellness solution for your pet's needs
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {categories.map((category, index) => {
              const IconComponent = category.icon;
              const linkUrl = `/products?category=${encodeURIComponent(category.slug)}`;
              return (
                <Link
                  key={index}
                  to={linkUrl}
                  className="bg-white rounded-2xl p-6 text-center hover:shadow-lg transition-all group"
                  data-testid={`category-${category.slug}`}
                >
                  <div 
                    className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform"
                    style={{ backgroundColor: `${category.color}15` }}
                  >
                    <IconComponent className="w-7 h-7" style={{ color: category.color }} />
                  </div>
                  <h3 className="font-semibold text-[#2D4A3E]">{category.name}</h3>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Best Sellers Section */}
      <section className="py-12 bg-[#FDF8F3] overflow-visible">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="inline-flex items-center gap-2 bg-[#C45C4A]/10 text-[#C45C4A] px-3 py-1.5 rounded-full text-sm font-medium mb-3">
                <TrendingUp className="w-4 h-4" />
                <span>Top Rated</span>
              </div>
              <h2 className="text-3xl font-bold text-[#2D4A3E] mb-1 font-['Fraunces']">
                Best Sellers
              </h2>
              <p className="text-[#5C6D5E] text-sm">
                Most loved products by our pet parent community
              </p>
            </div>
            <Link to="/products">
              <Button variant="outline" className="rounded-full" data-testid="view-bestsellers">
                View All
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-2xl p-4 animate-pulse">
                  <div className="bg-gray-200 h-64 rounded-xl mb-4"></div>
                  <div className="bg-gray-200 h-4 rounded w-3/4 mb-2"></div>
                  <div className="bg-gray-200 h-4 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : bestsellers.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-2xl">
              <p className="text-[#5C6D5E]">No products available yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {bestsellers.slice(0, 4).map((product, index) => (
                <div
                  key={product.id}
                  className="product-card animate-fade-in-up relative"
                  style={{ animationDelay: `${index * 0.1}s` }}
                  data-testid={`bestseller-card-${product.slug}`}
                >
                  {index === 0 && (
                    <div className="absolute -top-3 -left-3 z-10 bg-[#C45C4A] text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                      <Award className="w-3 h-3" />
                      #1 Best Seller
                    </div>
                  )}
                  <Link to={`/products/${product.slug}`}>
                    <div className="relative overflow-hidden">
                      <img
                        src={product.images?.[0] || "https://via.placeholder.com/400"}
                        alt={product.name}
                        className="product-image"
                      />
                      {product.compare_at_price && (
                        <span className="absolute top-4 left-4 bg-[#C45C4A] text-white px-3 py-1 rounded-full text-xs font-semibold">
                          Sale
                        </span>
                      )}
                    </div>
                  </Link>
                  <div className="p-4">
                    <div className="flex items-center gap-1 mb-2">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${i < Math.floor(product.rating) ? 'fill-[#D4A574] text-[#D4A574]' : 'text-[#E8DFD5]'}`}
                        />
                      ))}
                      <span className="text-xs text-[#5C6D5E] ml-1">({product.review_count})</span>
                    </div>
                    <Link to={`/products/${product.slug}`}>
                      <h3 className="font-semibold text-[#2D4A3E] mb-2 line-clamp-2 hover:text-[#D4A574] transition-colors">
                        {product.name}
                      </h3>
                    </Link>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-[#2D4A3E]">
                          ${product.price.toFixed(2)}
                        </span>
                        {product.compare_at_price && (
                          <span className="text-sm text-[#5C6D5E] line-through">
                            ${product.compare_at_price.toFixed(2)}
                          </span>
                        )}
                      </div>
                      <Button
                        size="sm"
                        className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] rounded-full"
                        onClick={(e) => {
                          e.preventDefault();
                          addToCart(product.id);
                        }}
                        data-testid={`bestseller-add-${product.slug}`}
                      >
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Loyalty Program Banner */}
      <section className="py-8 bg-gradient-to-r from-[#2D4A3E] to-[#3D5A4E]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4 text-white">
              <div className="w-12 h-12 rounded-full bg-[#D4A574] flex items-center justify-center flex-shrink-0">
                <Award className="w-6 h-6 text-[#2D4A3E]" />
              </div>
              <div>
                <h3 className="text-xl font-bold font-['Fraunces']">Wildly Ones Rewards</h3>
                <p className="text-white/80 text-sm">Earn points on every purchase, unlock exclusive perks</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-4 md:gap-6 text-white text-center">
              <div className="flex flex-col items-center">
                <span className="text-xl font-bold">1pt/$1</span>
                <span className="text-xs text-white/70">Points Earned</span>
              </div>
              <div className="hidden md:block w-px h-10 bg-white/30"></div>
              <div className="flex flex-col items-center">
                <span className="text-xl font-bold">100pts</span>
                <span className="text-xs text-white/70">= $5 Off</span>
              </div>
              <div className="hidden md:block w-px h-10 bg-white/30"></div>
              <div className="flex flex-col items-center">
                <span className="text-xl font-bold">4 Tiers</span>
                <span className="text-xs text-white/70">Bronze → Platinum</span>
              </div>
            </div>
            <Link to="/referral">
              <Button 
                className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] rounded-full font-semibold px-5"
                data-testid="join-rewards-btn"
              >
                Join Free
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Products / New Arrivals */}
      <section className="py-12 bg-[#E8DFD5]/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="inline-flex items-center gap-2 bg-[#6B8F71]/10 text-[#6B8F71] px-3 py-1.5 rounded-full text-sm font-medium mb-3">
                <Sparkles className="w-4 h-4" />
                <span>Just Added</span>
              </div>
              <h2 className="text-3xl font-bold text-[#2D4A3E] mb-1 font-['Fraunces']">
                New Arrivals
              </h2>
              <p className="text-[#5C6D5E] text-sm">
                Fresh additions to our wellness collection
              </p>
            </div>
            <Link to="/products">
              <Button variant="outline" className="rounded-full" data-testid="view-all-products">
                View All
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
          
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-2xl p-4 animate-pulse">
                  <div className="bg-gray-200 h-64 rounded-xl mb-4"></div>
                  <div className="bg-gray-200 h-4 rounded w-3/4 mb-2"></div>
                  <div className="bg-gray-200 h-4 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : featuredProducts.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-2xl">
              <p className="text-[#5C6D5E]">No products available yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {featuredProducts.slice(0, 4).map((product, index) => (
                <div
                  key={product.id}
                  className="product-card animate-fade-in-up"
                  style={{ animationDelay: `${index * 0.1}s` }}
                  data-testid={`product-card-${product.slug}`}
                >
                  <Link to={`/products/${product.slug}`}>
                    <div className="relative overflow-hidden">
                      <img
                        src={product.images?.[0] || "https://via.placeholder.com/400"}
                        alt={product.name}
                        className="product-image"
                      />
                      {product.compare_at_price && (
                        <span className="absolute top-4 left-4 bg-[#C45C4A] text-white px-3 py-1 rounded-full text-xs font-semibold">
                          Sale
                        </span>
                      )}
                    </div>
                  </Link>
                  <div className="p-4">
                    <div className="flex items-center gap-1 mb-2">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${i < Math.floor(product.rating) ? 'fill-[#D4A574] text-[#D4A574]' : 'text-[#E8DFD5]'}`}
                        />
                      ))}
                      <span className="text-xs text-[#5C6D5E] ml-1">({product.review_count})</span>
                    </div>
                    <Link to={`/products/${product.slug}`}>
                      <h3 className="font-semibold text-[#2D4A3E] mb-2 line-clamp-2 hover:text-[#D4A574] transition-colors">
                        {product.name}
                      </h3>
                    </Link>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-[#2D4A3E]">
                          ${product.price.toFixed(2)}
                        </span>
                        {product.compare_at_price && (
                          <span className="text-sm text-[#5C6D5E] line-through">
                            ${product.compare_at_price.toFixed(2)}
                          </span>
                        )}
                      </div>
                      <Button
                        size="sm"
                        className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] rounded-full"
                        onClick={(e) => {
                          e.preventDefault();
                          addToCart(product.id);
                        }}
                        data-testid={`add-to-cart-${product.slug}`}
                      >
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-[#2D4A3E] rounded-3xl p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <Heart className="w-96 h-96 absolute -right-20 -bottom-20" />
            </div>
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 font-['Fraunces']">
                Join the Wildly Ones Family
              </h2>
              <p className="text-white/80 text-lg mb-8 max-w-xl mx-auto">
                Sign up for 15% off your first order, plus exclusive tips on keeping your 
                furry friend happy and healthy.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/products">
                  <Button
                    className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] px-8 py-6 rounded-full font-semibold text-lg"
                    data-testid="cta-shop-btn"
                  >
                    Start Shopping
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
