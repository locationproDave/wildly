import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  Package, 
  DollarSign, 
  TrendingUp, 
  Trash2, 
  ChevronDown,
  Search,
  Filter,
  ExternalLink
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Badge } from "../components/ui/badge";

const PipelinePage = () => {
  const { token, API, user } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterVerdict, setFilterVerdict] = useState("all");

  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products/saved`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data);
    } catch (error) {
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const deleteProduct = async (productId) => {
    try {
      await axios.delete(`${API}/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(products.filter(p => p.id !== productId));
      toast.success("Product removed");
      fetchStats();
    } catch (error) {
      toast.error("Failed to delete product");
    }
  };

  const updateVerdict = async (productId, verdict) => {
    try {
      await axios.patch(
        `${API}/products/${productId}/verdict`,
        null,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { verdict }
        }
      );
      setProducts(products.map(p => 
        p.id === productId ? { ...p, verdict } : p
      ));
      toast.success("Verdict updated");
      fetchStats();
    } catch (error) {
      toast.error("Failed to update verdict");
    }
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.product_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.supplier?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterVerdict === "all" || product.verdict === filterVerdict;
    return matchesSearch && matchesFilter;
  });

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case "RECOMMEND":
        return "bg-[#768A75] text-white hover:bg-[#658364]";
      case "INVESTIGATE FURTHER":
        return "bg-[#E8B05C] text-[#2F3E32] hover:bg-[#d9a350]";
      case "SKIP":
        return "bg-[#D66D5A] text-white hover:bg-[#c95d4a]";
      default:
        return "bg-[#A8A29E] text-white";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-pulse-soft text-[#2F3E32]">Loading your pipeline...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-[#2F3E32] mb-2 font-['Fraunces']">
            Product Pipeline
          </h1>
          <p className="text-[#57534E]">
            Manage and track your sourced products
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="card-base p-6" data-testid="stat-saved-products">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[#2F3E32]/10 flex items-center justify-center">
                  <Package className="w-6 h-6 text-[#2F3E32]" />
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#2F3E32] font-['Fraunces']">
                    {stats.saved_products}
                  </p>
                  <p className="text-sm text-[#57534E]">Saved Products</p>
                </div>
              </div>
            </div>
            
            <div className="card-base p-6" data-testid="stat-total-searches">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[#D4A373]/20 flex items-center justify-center">
                  <Search className="w-6 h-6 text-[#D4A373]" />
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#2F3E32] font-['Fraunces']">
                    {stats.total_searches}
                  </p>
                  <p className="text-sm text-[#57534E]">Total Searches</p>
                </div>
              </div>
            </div>
            
            <div className="card-base p-6" data-testid="stat-recommended">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-[#768A75]/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-[#768A75]" />
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#2F3E32] font-['Fraunces']">
                    {stats.recommended_products}
                  </p>
                  <p className="text-sm text-[#57534E]">Recommended</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
            <Input
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-xl border-stone-200"
              data-testid="search-products-input"
            />
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="rounded-xl" data-testid="filter-dropdown">
                <Filter className="w-4 h-4 mr-2" />
                {filterVerdict === "all" ? "All Verdicts" : filterVerdict}
                <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilterVerdict("all")}>
                All Verdicts
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterVerdict("RECOMMEND")}>
                Recommend
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterVerdict("INVESTIGATE FURTHER")}>
                Investigate Further
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterVerdict("SKIP")}>
                Skip
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <Package className="w-8 h-8" />
            </div>
            <h3 className="empty-state-title">No products yet</h3>
            <p className="empty-state-description">
              Start researching products in the Research tab to build your pipeline.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map((product, index) => (
              <div
                key={product.id}
                className="product-card animate-fade-in-up"
                style={{ animationDelay: `${index * 0.05}s` }}
                data-testid={`product-card-${product.id}`}
              >
                {/* Header */}
                <div className="product-card-header">
                  <div className="flex-1 min-w-0">
                    <h3 className="product-card-title truncate">{product.product_name}</h3>
                    <p className="product-card-supplier">{product.supplier}</p>
                  </div>
                  <button
                    onClick={() => deleteProduct(product.id)}
                    className="text-[#A8A29E] hover:text-[#D66D5A] transition-colors p-2"
                    data-testid={`delete-product-${product.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Metrics */}
                <div className="space-y-1 mb-4">
                  {product.supplier_rating && (
                    <div className="product-card-metric">
                      <span className="product-card-metric-label">Rating</span>
                      <span className="product-card-metric-value">{product.supplier_rating}</span>
                    </div>
                  )}
                  {product.landed_cost && (
                    <div className="product-card-metric">
                      <span className="product-card-metric-label">Landed Cost</span>
                      <span className="product-card-metric-value">{product.landed_cost}</span>
                    </div>
                  )}
                  {product.recommended_retail_price && (
                    <div className="product-card-metric">
                      <span className="product-card-metric-label">Retail Price</span>
                      <span className="product-card-metric-value">{product.recommended_retail_price}</span>
                    </div>
                  )}
                  {product.gross_margin && (
                    <div className="product-card-metric">
                      <span className="product-card-metric-label">Margin</span>
                      <span className="product-card-metric-value font-semibold text-[#768A75]">
                        {product.gross_margin}
                      </span>
                    </div>
                  )}
                </div>

                {/* Emotional Angle */}
                {product.emotional_angle && (
                  <p className="text-sm text-[#57534E] italic mb-4 line-clamp-2">
                    "{product.emotional_angle}"
                  </p>
                )}

                {/* Verdict */}
                <div className="flex items-center justify-between">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        size="sm"
                        className={`verdict-badge ${getVerdictColor(product.verdict)}`}
                        data-testid={`verdict-btn-${product.id}`}
                      >
                        {product.verdict || "Set Verdict"}
                        <ChevronDown className="w-3 h-3 ml-1" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => updateVerdict(product.id, "RECOMMEND")}>
                        Recommend
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => updateVerdict(product.id, "INVESTIGATE FURTHER")}>
                        Investigate Further
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => updateVerdict(product.id, "SKIP")}>
                        Skip
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {product.us_warehouse === "Yes" && (
                    <Badge variant="outline" className="text-[#768A75] border-[#768A75]">
                      US Warehouse
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PipelinePage;
