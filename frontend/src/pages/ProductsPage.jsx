import React, { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import axios from "axios";
import { useCart } from "../App";
import { 
  Search, 
  Filter, 
  Star, 
  Dog, 
  Cat,
  X,
  ChevronDown
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ProductsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState(searchParams.get("search") || "");
  const { addToCart } = useCart();

  const currentCategory = searchParams.get("category") || "";
  const currentPetType = searchParams.get("pet_type") || "";

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, [searchParams]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (currentCategory) params.append("category", currentCategory);
      if (currentPetType) params.append("pet_type", currentPetType);
      if (searchQuery) params.append("search", searchQuery);

      const response = await axios.get(`${BACKEND_URL}/api/products?${params.toString()}`);
      setProducts(response.data);
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/products/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    const newParams = new URLSearchParams(searchParams);
    if (searchQuery) {
      newParams.set("search", searchQuery);
    } else {
      newParams.delete("search");
    }
    setSearchParams(newParams);
  };

  const setFilter = (key, value) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams({});
    setSearchQuery("");
  };

  const hasFilters = currentCategory || currentPetType || searchQuery;

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-[#2D4A3E] mb-2 font-['Fraunces']">
            Our Products
          </h1>
          <p className="text-[#5C6D5E]">
            Premium pet wellness products designed with love
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#5C6D5E]" />
            <Input
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-full border-[#E8DFD5]"
              data-testid="search-input"
            />
          </form>

          {/* Category Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="rounded-full" data-testid="category-filter">
                <Filter className="w-4 h-4 mr-2" />
                {currentCategory || "All Categories"}
                <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilter("category", "")}>
                All Categories
              </DropdownMenuItem>
              {categories.map((cat) => (
                <DropdownMenuItem key={cat} onClick={() => setFilter("category", cat)}>
                  {cat}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Pet Type Filter */}
          <div className="flex gap-2">
            <Button
              variant={currentPetType === "dog" ? "default" : "outline"}
              className={`rounded-full ${currentPetType === "dog" ? "bg-[#2D4A3E]" : ""}`}
              onClick={() => setFilter("pet_type", currentPetType === "dog" ? "" : "dog")}
              data-testid="filter-dog"
            >
              <Dog className="w-4 h-4 mr-2" />
              Dogs
            </Button>
            <Button
              variant={currentPetType === "cat" ? "default" : "outline"}
              className={`rounded-full ${currentPetType === "cat" ? "bg-[#2D4A3E]" : ""}`}
              onClick={() => setFilter("pet_type", currentPetType === "cat" ? "" : "cat")}
              data-testid="filter-cat"
            >
              <Cat className="w-4 h-4 mr-2" />
              Cats
            </Button>
          </div>

          {hasFilters && (
            <Button
              variant="ghost"
              className="rounded-full text-[#C45C4A]"
              onClick={clearFilters}
              data-testid="clear-filters"
            >
              <X className="w-4 h-4 mr-2" />
              Clear
            </Button>
          )}
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl p-4 animate-pulse">
                <div className="bg-gray-200 h-64 rounded-xl mb-4"></div>
                <div className="bg-gray-200 h-4 rounded w-3/4 mb-2"></div>
                <div className="bg-gray-200 h-4 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-[#E8DFD5] rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-10 h-10 text-[#5C6D5E]" />
            </div>
            <h3 className="text-xl font-semibold text-[#2D4A3E] mb-2 font-['Fraunces']">
              No products found
            </h3>
            <p className="text-[#5C6D5E] mb-6">
              Try adjusting your filters or search terms
            </p>
            <Button onClick={clearFilters} className="rounded-full">
              Clear Filters
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product, index) => (
              <div
                key={product.id}
                className="product-card animate-fade-in-up"
                style={{ animationDelay: `${index * 0.05}s` }}
                data-testid={`product-${product.slug}`}
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
                    <div className="absolute top-4 right-4 flex gap-1">
                      {(product.pet_type === "dog" || product.pet_type === "both") && (
                        <span className="bg-white/90 p-1.5 rounded-full">
                          <Dog className="w-4 h-4 text-[#2D4A3E]" />
                        </span>
                      )}
                      {(product.pet_type === "cat" || product.pet_type === "both") && (
                        <span className="bg-white/90 p-1.5 rounded-full">
                          <Cat className="w-4 h-4 text-[#2D4A3E]" />
                        </span>
                      )}
                    </div>
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
                    <h3 className="font-semibold text-[#2D4A3E] mb-1 line-clamp-2 hover:text-[#D4A574] transition-colors">
                      {product.name}
                    </h3>
                  </Link>
                  <p className="text-sm text-[#5C6D5E] mb-3 line-clamp-2">
                    {product.short_description}
                  </p>
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
                      data-testid={`add-${product.slug}`}
                    >
                      Add to Cart
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductsPage;
