import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import AdminSidebar from "../components/admin/AdminSidebar";
import {
  Search,
  Filter,
  Package,
  DollarSign,
  TrendingUp,
  Star,
  Truck,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Import,
  Calculator,
  ExternalLink,
  Warehouse,
  ShoppingBag,
  RefreshCw,
  X,
  Sparkles,
  Lightbulb,
  Target,
  Zap
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Slider } from "../components/ui/slider";
import { Textarea } from "../components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminSourcingPage = () => {
  const { token } = useAuth();
  const API = `${BACKEND_URL}/api`;

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [petType, setPetType] = useState("all");
  const [productType, setProductType] = useState("all");
  const [supplier, setSupplier] = useState("all");
  const [priceRange, setPriceRange] = useState([0, 100]);
  const [showFilters, setShowFilters] = useState(false);

  // Data State
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Import Dialog State
  const [importDialog, setImportDialog] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [customName, setCustomName] = useState("");
  const [customPrice, setCustomPrice] = useState("");
  const [customDescription, setCustomDescription] = useState("");
  const [importing, setImporting] = useState(false);

  // Profit Calculator State
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [calcProduct, setCalcProduct] = useState(null);
  const [calcRetailPrice, setCalcRetailPrice] = useState(0);

  // AI Recommendations State
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [showRecs, setShowRecs] = useState(true);

  useEffect(() => {
    fetchCategories();
    fetchRecommendations();
  }, []);

  useEffect(() => {
    searchProducts();
  }, [page]);

  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const response = await axios.get(`${API}/admin/sourcing/ai-recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error("Error fetching recommendations:", error);
    } finally {
      setLoadingRecs(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/admin/sourcing/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const searchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/admin/sourcing/search`,
        {
          query: searchQuery,
          pet_type: petType,
          product_type: productType,
          supplier: supplier,
          min_price: priceRange[0],
          max_price: priceRange[1],
          page: page,
          limit: 12
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setProducts(response.data.products || []);
      setTotalPages(response.data.total_pages || 1);
      setTotal(response.data.total || 0);
    } catch (error) {
      toast.error("Failed to search products");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    setPage(1);
    searchProducts();
  };

  const applyRecommendation = (rec) => {
    setSearchQuery(rec.suggested_search);
    if (rec.pet_type !== "all") setPetType(rec.pet_type);
    if (rec.category) setProductType(rec.category);
    setPage(1);
    setTimeout(() => searchProducts(), 100);
    toast.success(`Searching: "${rec.suggested_search}"`);
  };

  const openImportDialog = (product) => {
    setSelectedProduct(product);
    setCustomName(product.name);
    setCustomPrice(product.suggested_retail?.toString() || "");
    setCustomDescription("");
    setImportDialog(true);
  };

  const handleImport = async () => {
    if (!selectedProduct) return;
    
    setImporting(true);
    try {
      const response = await axios.post(
        `${API}/admin/sourcing/import`,
        {
          sourced_product: selectedProduct,
          custom_name: customName || null,
          custom_price: customPrice ? parseFloat(customPrice) : null,
          custom_description: customDescription || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Product "${customName}" imported to your store!`);
      setImportDialog(false);
      setSelectedProduct(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to import product");
    } finally {
      setImporting(false);
    }
  };

  const openCalculator = (product) => {
    setCalcProduct(product);
    setCalcRetailPrice(product.suggested_retail || 0);
    setCalculatorOpen(true);
  };

  const calculateProfit = () => {
    if (!calcProduct) return null;
    const landedCost = calcProduct.landed_cost || 0;
    const retail = calcRetailPrice;
    const grossMargin = retail - landedCost;
    const marginPercent = retail > 0 ? (grossMargin / retail) * 100 : 0;
    const paymentFees = retail * 0.029 + 0.30;
    const marketingEstimate = retail * 0.20;
    const netProfit = grossMargin - paymentFees - marketingEstimate;
    const netMargin = retail > 0 ? (netProfit / retail) * 100 : 0;
    
    return {
      landedCost,
      retail,
      grossMargin,
      marginPercent,
      paymentFees,
      marketingEstimate,
      netProfit,
      netMargin
    };
  };

  const profitMetrics = calculateProfit();

  const getMarginColor = (margin) => {
    if (margin >= 60) return "text-green-600";
    if (margin >= 40) return "text-yellow-600";
    return "text-red-600";
  };

  const getSupplierBadgeColor = (supplierName) => {
    switch (supplierName?.toLowerCase()) {
      case "faire":
        return "bg-emerald-100 text-emerald-800";
      case "zendrop":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <AdminSidebar>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[#2F3E32] font-['Fraunces']">
              Product Sourcing
            </h1>
            <p className="text-[#5C6D5E] mt-1">
              Find and import products from verified suppliers
            </p>
          </div>
          
          <Badge variant="outline" className="py-2 px-3 w-fit">
            <Package className="w-4 h-4 mr-2" />
            {total} Products Found
          </Badge>
        </div>

        {/* AI Recommendations */}
        {showRecs && recommendations && (
          <div className="bg-gradient-to-r from-[#2D4A3E] to-[#3D5A4E] rounded-2xl shadow-lg p-6 mb-8 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-semibold text-lg">AI Product Recommendations</h2>
                  <p className="text-white/70 text-sm">Based on your store performance & trends</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-white/70 hover:text-white hover:bg-white/10"
                onClick={() => setShowRecs(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            
            {loadingRecs ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="ml-2">Analyzing your store...</span>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                  {recommendations?.recommendations?.slice(0, 6).map((rec, idx) => (
                    <button
                      key={idx}
                      onClick={() => applyRecommendation(rec)}
                      className="text-left p-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all group"
                      data-testid={`ai-rec-${idx}`}
                    >
                      <div className="flex items-start gap-2">
                        {rec.type === "trending" && <TrendingUp className="w-4 h-4 mt-0.5 text-yellow-300" />}
                        {rec.type === "similar_to_bestseller" && <Target className="w-4 h-4 mt-0.5 text-green-300" />}
                        {rec.type === "seasonal" && <Zap className="w-4 h-4 mt-0.5 text-blue-300" />}
                        {rec.type === "gap_fill" && <Lightbulb className="w-4 h-4 mt-0.5 text-orange-300" />}
                        <div className="flex-1">
                          <p className="text-sm font-medium line-clamp-2">{rec.reason}</p>
                          <p className="text-xs text-white/60 mt-1 flex items-center gap-1">
                            <Search className="w-3 h-3" />
                            {rec.suggested_search}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                
                {recommendations?.insights && (
                  <div className="flex items-center gap-2 text-sm text-white/80 bg-white/10 rounded-lg px-3 py-2">
                    <Lightbulb className="w-4 h-4 text-yellow-300" />
                    {recommendations.insights.suggestion}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Search & Filters */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E8E6DE] p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            {/* Main Search */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search products (e.g., calming dog treats, cat bed, fish tank)"
                  className="pl-10 h-12 rounded-xl border-[#E8E6DE]"
                  data-testid="sourcing-search-input"
                />
              </div>
              
              <Button
                type="submit"
                className="h-12 px-6 bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
                disabled={loading}
                data-testid="sourcing-search-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Search
                  </>
                )}
              </Button>
              
              <Button
                type="button"
                variant="outline"
                className="h-12 px-4 rounded-xl"
                onClick={() => setShowFilters(!showFilters)}
                data-testid="sourcing-filter-toggle"
              >
                <Filter className="w-5 h-5 mr-2" />
                Filters
                <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
              </Button>
            </div>

            {/* Expandable Filters */}
            {showFilters && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-[#E8E6DE]">
                {/* Pet Type */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Pet Type
                  </label>
                  <Select value={petType} onValueChange={setPetType}>
                    <SelectTrigger className="rounded-xl" data-testid="sourcing-pet-filter">
                      <SelectValue placeholder="All Pets" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories?.pet_types?.map((pt) => (
                        <SelectItem key={pt.value} value={pt.value}>
                          {pt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Product Category */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Category
                  </label>
                  <Select value={productType} onValueChange={setProductType}>
                    <SelectTrigger className="rounded-xl" data-testid="sourcing-category-filter">
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories?.product_types?.map((ct) => (
                        <SelectItem key={ct.value} value={ct.value}>
                          {ct.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Supplier */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Supplier
                  </label>
                  <Select value={supplier} onValueChange={setSupplier}>
                    <SelectTrigger className="rounded-xl" data-testid="sourcing-supplier-filter">
                      <SelectValue placeholder="All Suppliers" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories?.suppliers?.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Price Range */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Max Cost: ${priceRange[1]}
                  </label>
                  <Slider
                    value={priceRange}
                    onValueChange={setPriceRange}
                    min={0}
                    max={200}
                    step={5}
                    className="mt-4"
                  />
                </div>
              </div>
            )}
          </form>
        </div>

        {/* Results Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#2D4A3E]" />
            <span className="ml-3 text-[#5C6D5E]">Searching suppliers...</span>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-[#E8E6DE]">
            <Package className="w-16 h-16 mx-auto text-[#D4D4D4] mb-4" />
            <h3 className="text-xl font-semibold text-[#2F3E32] mb-2">No products found</h3>
            <p className="text-[#5C6D5E] mb-6">Try adjusting your search or filters</p>
            <Button
              onClick={() => {
                setSearchQuery("");
                setPetType("all");
                setProductType("all");
                setSupplier("all");
                setPriceRange([0, 100]);
                handleSearch();
              }}
              variant="outline"
              className="rounded-xl"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reset Filters
            </Button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {products.map((product) => (
                <div
                  key={product.id}
                  className="bg-white rounded-2xl border border-[#E8E6DE] overflow-hidden hover:shadow-lg transition-shadow"
                  data-testid={`sourced-product-${product.id}`}
                >
                  {/* Product Image */}
                  <div className="relative aspect-square bg-[#F5F5F5]">
                    <img
                      src={product.image || "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=400"}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Supplier Badge */}
                    <span className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-medium ${getSupplierBadgeColor(product.supplier)}`}>
                      {product.supplier}
                    </span>
                    
                    {/* US Warehouse Badge */}
                    {product.us_warehouse && (
                      <span className="absolute top-3 right-3 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
                        <Warehouse className="w-3 h-3" />
                        US
                      </span>
                    )}
                  </div>

                  {/* Product Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-[#2F3E32] mb-2 line-clamp-2">
                      {product.name}
                    </h3>

                    {/* Rating & Orders */}
                    <div className="flex items-center gap-4 text-sm text-[#5C6D5E] mb-3">
                      <span className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                        {product.rating}
                      </span>
                      <span className="flex items-center gap-1">
                        <ShoppingBag className="w-4 h-4" />
                        {product.orders_fulfilled?.toLocaleString()} sold
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {product.processing_days}d
                      </span>
                    </div>

                    {/* Pricing */}
                    <div className="bg-[#F8F7F4] rounded-xl p-3 mb-4">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-[#5C6D5E]">Cost:</span>
                          <span className="font-semibold text-[#2F3E32] ml-1">
                            ${product.supplier_cost?.toFixed(2)}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#5C6D5E]">Shipping:</span>
                          <span className="font-semibold text-[#2F3E32] ml-1">
                            {product.shipping_cost === 0 ? "Free" : `$${product.shipping_cost?.toFixed(2)}`}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#5C6D5E]">Landed:</span>
                          <span className="font-semibold text-[#2F3E32] ml-1">
                            ${product.landed_cost?.toFixed(2)}
                          </span>
                        </div>
                        <div>
                          <span className="text-[#5C6D5E]">Retail:</span>
                          <span className="font-semibold text-[#2F3E32] ml-1">
                            ${product.suggested_retail?.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      
                      {/* Margin */}
                      <div className="mt-2 pt-2 border-t border-[#E8E6DE] flex items-center justify-between">
                        <span className="text-[#5C6D5E] text-sm">Margin:</span>
                        <span className={`font-bold ${getMarginColor(product.margin_percent)}`}>
                          {product.margin_percent?.toFixed(0)}% (${product.margin?.toFixed(2)})
                        </span>
                      </div>
                    </div>

                    {/* Features */}
                    {product.features && product.features.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {product.features.slice(0, 3).map((feature, idx) => (
                          <span key={idx} className="text-xs bg-[#F2F0E9] text-[#5C6D5E] px-2 py-1 rounded-full">
                            {feature}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        onClick={() => openImportDialog(product)}
                        className="flex-1 bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
                        data-testid={`import-btn-${product.id}`}
                      >
                        <Import className="w-4 h-4 mr-2" />
                        Import
                      </Button>
                      <Button
                        onClick={() => openCalculator(product)}
                        variant="outline"
                        className="rounded-xl"
                        data-testid={`calc-btn-${product.id}`}
                      >
                        <Calculator className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-xl"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                
                <span className="px-4 py-2 text-[#5C6D5E]">
                  Page {page} of {totalPages}
                </span>
                
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="rounded-xl"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </>
        )}

        {/* Import Dialog */}
        <Dialog open={importDialog} onOpenChange={setImportDialog}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="font-['Fraunces']">Import Product</DialogTitle>
              <DialogDescription>
                Customize the product details before importing to your store
              </DialogDescription>
            </DialogHeader>
            
            {selectedProduct && (
              <div className="space-y-4">
                {/* Preview */}
                <div className="flex gap-4 p-4 bg-[#F8F7F4] rounded-xl">
                  <img
                    src={selectedProduct.image}
                    alt={selectedProduct.name}
                    className="w-20 h-20 object-cover rounded-lg"
                  />
                  <div className="flex-1">
                    <p className="text-sm text-[#5C6D5E]">{selectedProduct.supplier}</p>
                    <p className="font-medium text-[#2F3E32]">{selectedProduct.name}</p>
                    <p className="text-sm text-[#5C6D5E]">
                      Cost: ${selectedProduct.landed_cost?.toFixed(2)} | Suggested: ${selectedProduct.suggested_retail?.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Custom Name */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Product Name
                  </label>
                  <Input
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    className="rounded-xl"
                    data-testid="import-name-input"
                  />
                </div>

                {/* Custom Price */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Retail Price ($)
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    value={customPrice}
                    onChange={(e) => setCustomPrice(e.target.value)}
                    className="rounded-xl"
                    data-testid="import-price-input"
                  />
                  {customPrice && (
                    <p className="text-sm text-[#5C6D5E] mt-1">
                      Margin: {((parseFloat(customPrice) - selectedProduct.landed_cost) / parseFloat(customPrice) * 100).toFixed(0)}%
                    </p>
                  )}
                </div>

                {/* Custom Description */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Custom Description (optional)
                  </label>
                  <Textarea
                    value={customDescription}
                    onChange={(e) => setCustomDescription(e.target.value)}
                    placeholder="Leave blank to auto-generate"
                    className="rounded-xl"
                    rows={3}
                    data-testid="import-description-input"
                  />
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setImportDialog(false)}
                className="rounded-xl"
              >
                Cancel
              </Button>
              <Button
                onClick={handleImport}
                disabled={importing || !customName}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
                data-testid="confirm-import-btn"
              >
                {importing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Import to Store
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Profit Calculator Dialog */}
        <Dialog open={calculatorOpen} onOpenChange={setCalculatorOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="font-['Fraunces'] flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Profit Calculator
              </DialogTitle>
            </DialogHeader>
            
            {calcProduct && profitMetrics && (
              <div className="space-y-4">
                <p className="text-sm text-[#5C6D5E]">{calcProduct.name}</p>
                
                {/* Retail Price Slider */}
                <div>
                  <label className="text-sm font-medium text-[#2F3E32] mb-2 block">
                    Retail Price: ${calcRetailPrice.toFixed(2)}
                  </label>
                  <Slider
                    value={[calcRetailPrice]}
                    onValueChange={([v]) => setCalcRetailPrice(v)}
                    min={calcProduct.landed_cost}
                    max={calcProduct.landed_cost * 5}
                    step={1}
                  />
                </div>

                {/* Metrics */}
                <div className="space-y-2 bg-[#F8F7F4] rounded-xl p-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#5C6D5E]">Landed Cost</span>
                    <span className="font-medium">${profitMetrics.landedCost.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#5C6D5E]">Gross Margin</span>
                    <span className={`font-medium ${getMarginColor(profitMetrics.marginPercent)}`}>
                      ${profitMetrics.grossMargin.toFixed(2)} ({profitMetrics.marginPercent.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#5C6D5E]">Payment Fees (~3%)</span>
                    <span className="font-medium text-red-600">-${profitMetrics.paymentFees.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#5C6D5E]">Marketing (~20%)</span>
                    <span className="font-medium text-red-600">-${profitMetrics.marketingEstimate.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm pt-2 border-t border-[#E8E6DE]">
                    <span className="font-semibold text-[#2F3E32]">Net Profit</span>
                    <span className={`font-bold ${profitMetrics.netProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${profitMetrics.netProfit.toFixed(2)} ({profitMetrics.netMargin.toFixed(0)}%)
                    </span>
                  </div>
                </div>

                {/* Recommendation */}
                <div className={`p-3 rounded-xl ${profitMetrics.netMargin >= 15 ? 'bg-green-50 text-green-800' : 'bg-yellow-50 text-yellow-800'}`}>
                  {profitMetrics.netMargin >= 15 ? (
                    <p className="text-sm flex items-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Good margin! This price point looks profitable.
                    </p>
                  ) : (
                    <p className="text-sm flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      Consider a higher price for better profitability.
                    </p>
                  )}
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setCalculatorOpen(false)}
                className="rounded-xl"
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  setCalculatorOpen(false);
                  setCustomPrice(calcRetailPrice.toString());
                  openImportDialog(calcProduct);
                }}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-xl"
              >
                Import at ${calcRetailPrice.toFixed(2)}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AdminSidebar>
  );
};

export default AdminSourcingPage;
