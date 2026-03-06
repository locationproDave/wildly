import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { 
  Package, 
  Plus, 
  Search,
  Edit,
  Trash2,
  ChevronLeft,
  X,
  Image as ImageIcon,
  Check,
  AlertCircle,
  Dog,
  Cat,
  Bird,
  Fish,
  Squirrel
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PET_TYPES = [
  { value: "dog", label: "Dog", icon: Dog },
  { value: "cat", label: "Cat", icon: Cat },
  { value: "both", label: "Dogs & Cats", icon: Dog },
  { value: "bird", label: "Bird", icon: Bird },
  { value: "fish", label: "Fish", icon: Fish },
  { value: "rabbit", label: "Rabbit", icon: Squirrel },
  { value: "reptile", label: "Reptile", icon: Squirrel },
  { value: "small_pet", label: "Small Pet", icon: Squirrel }
];

const CATEGORIES = [
  "supplements",
  "beds",
  "calming",
  "grooming",
  "food",
  "toys",
  "habitat",
  "accessories"
];

const emptyProduct = {
  name: "",
  slug: "",
  description: "",
  short_description: "",
  price: 0,
  compare_at_price: null,
  cost: 0,
  category: "supplements",
  subcategory: "",
  images: [],
  tags: [],
  pet_type: "dog",
  in_stock: true,
  stock_quantity: 100,
  supplier: "",
  supplier_sku: "",
  features: [],
  ingredients: "",
  dimensions: "",
  weight: "",
  rating: 4.5,
  review_count: 0
};

const AdminProductsPage = () => {
  const { token } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [petTypeFilter, setPetTypeFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState(emptyProduct);
  const [saving, setSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, [search, petTypeFilter, categoryFilter]);

  const fetchProducts = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (petTypeFilter) params.append("pet_type", petTypeFilter);
      if (categoryFilter) params.append("category", categoryFilter);
      
      const response = await axios.get(`${BACKEND_URL}/api/admin/products?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data);
    } catch (error) {
      console.error("Error fetching products:", error);
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      ...emptyProduct,
      ...product,
      tags: product.tags || [],
      features: product.features || [],
      images: product.images || []
    });
    setIsDialogOpen(true);
  };

  const handleCreate = () => {
    setEditingProduct(null);
    setFormData(emptyProduct);
    setIsDialogOpen(true);
  };

  const generateSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleNameChange = (name) => {
    setFormData(prev => ({
      ...prev,
      name,
      slug: editingProduct ? prev.slug : generateSlug(name)
    }));
  };

  const handleSave = async () => {
    if (!formData.name || !formData.slug || !formData.price) {
      toast.error("Please fill in required fields (name, slug, price)");
      return;
    }

    setSaving(true);
    try {
      if (editingProduct) {
        await axios.put(
          `${BACKEND_URL}/api/admin/products/${editingProduct.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success("Product updated successfully");
      } else {
        await axios.post(
          `${BACKEND_URL}/api/admin/products`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        toast.success("Product created successfully");
      }
      setIsDialogOpen(false);
      fetchProducts();
    } catch (error) {
      console.error("Error saving product:", error);
      toast.error(error.response?.data?.detail || "Failed to save product");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (productId) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/admin/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Product deleted");
      setDeleteConfirm(null);
      fetchProducts();
    } catch (error) {
      console.error("Error deleting product:", error);
      toast.error("Failed to delete product");
    }
  };

  const handleArrayInput = (field, value) => {
    const items = value.split(",").map(item => item.trim()).filter(Boolean);
    setFormData(prev => ({ ...prev, [field]: items }));
  };

  const getPetIcon = (petType) => {
    const pet = PET_TYPES.find(p => p.value === petType);
    if (pet) {
      const Icon = pet.icon;
      return <Icon className="w-4 h-4" />;
    }
    return <Package className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link to="/admin">
              <Button variant="ghost" size="icon" className="rounded-full">
                <ChevronLeft className="w-5 h-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-[#2D4A3E] font-['Fraunces']" data-testid="page-title">
                Product Management
              </h1>
              <p className="text-[#5C6D5E]">{products.length} products</p>
            </div>
          </div>
          <Button 
            onClick={handleCreate}
            className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
            data-testid="add-product-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Product
          </Button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl p-4 mb-6 shadow-sm">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#5C6D5E] w-4 h-4" />
                <Input
                  placeholder="Search products..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 rounded-full border-[#E8DFD5]"
                  data-testid="search-input"
                />
              </div>
            </div>
            <Select value={petTypeFilter || "all"} onValueChange={(v) => setPetTypeFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[150px] rounded-full border-[#E8DFD5]" data-testid="pet-type-filter">
                <SelectValue placeholder="Pet Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Pets</SelectItem>
                {PET_TYPES.map(pet => (
                  <SelectItem key={pet.value} value={pet.value}>{pet.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryFilter || "all"} onValueChange={(v) => setCategoryFilter(v === "all" ? "" : v)}>
              <SelectTrigger className="w-[150px] rounded-full border-[#E8DFD5]" data-testid="category-filter">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {(search || petTypeFilter || categoryFilter) && (
              <Button 
                variant="ghost" 
                onClick={() => { setSearch(""); setPetTypeFilter(""); setCategoryFilter(""); }}
                className="text-[#5C6D5E]"
              >
                Clear filters
              </Button>
            )}
          </div>
        </div>

        {/* Products Table */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="p-12 text-center">
              <Package className="w-12 h-12 text-[#5C6D5E] mx-auto mb-4" />
              <p className="text-[#5C6D5E]">No products found</p>
              <Button onClick={handleCreate} className="mt-4 bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full">
                <Plus className="w-4 h-4 mr-2" /> Add First Product
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#FDF8F3] border-b border-[#E8DFD5]">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-[#2D4A3E]">Product</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-[#2D4A3E]">Price</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-[#2D4A3E]">Category</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-[#2D4A3E]">Pet Type</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-[#2D4A3E]">Stock</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-[#2D4A3E]">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E8DFD5]">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-[#FDF8F3] transition-colors" data-testid={`product-row-${product.id}`}>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-lg bg-[#E8DFD5] overflow-hidden flex-shrink-0">
                            {product.images?.[0] ? (
                              <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <ImageIcon className="w-5 h-5 text-[#5C6D5E]" />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-[#2D4A3E] line-clamp-1">{product.name}</p>
                            <p className="text-xs text-[#5C6D5E]">{product.slug}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-[#2D4A3E]">${product.price?.toFixed(2)}</p>
                        {product.compare_at_price && (
                          <p className="text-xs text-[#5C6D5E] line-through">${product.compare_at_price?.toFixed(2)}</p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary" className="bg-[#E8DFD5] text-[#2D4A3E] capitalize">
                          {product.category}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getPetIcon(product.pet_type)}
                          <span className="text-[#5C6D5E] capitalize">{product.pet_type?.replace('_', ' ')}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {product.in_stock ? (
                          <Badge className="bg-green-100 text-green-800">
                            <Check className="w-3 h-3 mr-1" />
                            {product.stock_quantity}
                          </Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Out
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(product)}
                            className="rounded-full hover:bg-[#E8DFD5]"
                            data-testid={`edit-btn-${product.id}`}
                          >
                            <Edit className="w-4 h-4 text-[#2D4A3E]" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeleteConfirm(product.id)}
                            className="rounded-full hover:bg-red-100"
                            data-testid={`delete-btn-${product.id}`}
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Delete Confirmation Dialog */}
        <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E]">Delete Product</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this product? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setDeleteConfirm(null)} className="rounded-full">
                Cancel
              </Button>
              <Button 
                onClick={() => handleDelete(deleteConfirm)}
                className="bg-red-600 hover:bg-red-700 rounded-full"
              >
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Create/Edit Product Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E] font-['Fraunces']">
                {editingProduct ? "Edit Product" : "Add New Product"}
              </DialogTitle>
              <DialogDescription>
                {editingProduct ? "Update product details" : "Create a new product for your store"}
              </DialogDescription>
            </DialogHeader>
            
            <div className="grid gap-4 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Product name"
                    className="rounded-lg"
                    data-testid="product-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="slug">Slug *</Label>
                  <Input
                    id="slug"
                    value={formData.slug}
                    onChange={(e) => setFormData(prev => ({ ...prev, slug: e.target.value }))}
                    placeholder="product-slug"
                    className="rounded-lg"
                    data-testid="product-slug-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="short_description">Short Description</Label>
                <Input
                  id="short_description"
                  value={formData.short_description}
                  onChange={(e) => setFormData(prev => ({ ...prev, short_description: e.target.value }))}
                  placeholder="Brief product summary"
                  className="rounded-lg"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Full Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Detailed product description"
                  rows={3}
                  className="rounded-lg"
                />
              </div>

              {/* Pricing */}
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="price">Price * ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                    className="rounded-lg"
                    data-testid="product-price-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="compare_at_price">Compare At ($)</Label>
                  <Input
                    id="compare_at_price"
                    type="number"
                    step="0.01"
                    value={formData.compare_at_price || ""}
                    onChange={(e) => setFormData(prev => ({ ...prev, compare_at_price: parseFloat(e.target.value) || null }))}
                    className="rounded-lg"
                    placeholder="Original price"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cost">Cost ($)</Label>
                  <Input
                    id="cost"
                    type="number"
                    step="0.01"
                    value={formData.cost}
                    onChange={(e) => setFormData(prev => ({ ...prev, cost: parseFloat(e.target.value) || 0 }))}
                    className="rounded-lg"
                  />
                </div>
              </div>

              {/* Category & Pet Type */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category *</Label>
                  <Select 
                    value={formData.category} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                  >
                    <SelectTrigger className="rounded-lg" data-testid="product-category-select">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map(cat => (
                        <SelectItem key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Pet Type *</Label>
                  <Select 
                    value={formData.pet_type} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, pet_type: value }))}
                  >
                    <SelectTrigger className="rounded-lg" data-testid="product-pet-type-select">
                      <SelectValue placeholder="Select pet type" />
                    </SelectTrigger>
                    <SelectContent>
                      {PET_TYPES.map(pet => (
                        <SelectItem key={pet.value} value={pet.value}>{pet.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Stock */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="stock_quantity">Stock Quantity</Label>
                  <Input
                    id="stock_quantity"
                    type="number"
                    value={formData.stock_quantity}
                    onChange={(e) => setFormData(prev => ({ ...prev, stock_quantity: parseInt(e.target.value) || 0 }))}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label>In Stock</Label>
                  <Select 
                    value={formData.in_stock ? "true" : "false"} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, in_stock: value === "true" }))}
                  >
                    <SelectTrigger className="rounded-lg">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Yes - In Stock</SelectItem>
                      <SelectItem value="false">No - Out of Stock</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Images */}
              <div className="space-y-2">
                <Label htmlFor="images">Image URLs (comma separated)</Label>
                <Textarea
                  id="images"
                  value={formData.images?.join(", ") || ""}
                  onChange={(e) => handleArrayInput("images", e.target.value)}
                  placeholder="https://example.com/image1.jpg, https://example.com/image2.jpg"
                  rows={2}
                  className="rounded-lg"
                />
              </div>

              {/* Tags & Features */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tags">Tags (comma separated)</Label>
                  <Input
                    id="tags"
                    value={formData.tags?.join(", ") || ""}
                    onChange={(e) => handleArrayInput("tags", e.target.value)}
                    placeholder="calming, anxiety, natural"
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="features">Features (comma separated)</Label>
                  <Input
                    id="features"
                    value={formData.features?.join(", ") || ""}
                    onChange={(e) => handleArrayInput("features", e.target.value)}
                    placeholder="Natural ingredients, Fast-acting"
                    className="rounded-lg"
                  />
                </div>
              </div>

              {/* Additional Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ingredients">Ingredients</Label>
                  <Textarea
                    id="ingredients"
                    value={formData.ingredients || ""}
                    onChange={(e) => setFormData(prev => ({ ...prev, ingredients: e.target.value }))}
                    rows={2}
                    className="rounded-lg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="supplier">Supplier Info</Label>
                  <Input
                    id="supplier"
                    value={formData.supplier || ""}
                    onChange={(e) => setFormData(prev => ({ ...prev, supplier: e.target.value }))}
                    placeholder="Supplier name"
                    className="rounded-lg"
                  />
                </div>
              </div>
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)} className="rounded-full">
                Cancel
              </Button>
              <Button 
                onClick={handleSave} 
                disabled={saving}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
                data-testid="save-product-btn"
              >
                {saving ? "Saving..." : (editingProduct ? "Update Product" : "Create Product")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminProductsPage;
