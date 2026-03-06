import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import axios from "axios";
import { 
  ChevronLeft,
  Users,
  Crown,
  Heart,
  AlertTriangle,
  Sparkles,
  Moon,
  Send,
  Mail,
  DollarSign,
  ShoppingBag,
  Eye,
  Zap,
  ChevronRight
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SEGMENT_ICONS = {
  vip: Crown,
  loyal: Heart,
  at_risk: AlertTriangle,
  new: Sparkles,
  dormant: Moon
};

const AdminCustomerSegmentsPage = () => {
  const { token } = useAuth();
  const [segments, setSegments] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [campaignDialog, setCampaignDialog] = useState(null);
  const [campaignData, setCampaignData] = useState(null);
  const [sendingCampaign, setSendingCampaign] = useState(false);
  const [customCampaign, setCustomCampaign] = useState({
    subject: "",
    message: "",
    promo_code: "",
    discount: ""
  });

  useEffect(() => {
    fetchSegments();
  }, []);

  const fetchSegments = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/admin/customer-segments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSegments(response.data.segments);
      setSummary(response.data.summary);
    } catch (error) {
      console.error("Error fetching segments:", error);
      toast.error("Failed to load customer segments");
    } finally {
      setLoading(false);
    }
  };

  const generateCampaign = async (segment) => {
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/customer-segments/${segment}/campaign`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCampaignData(response.data);
      setCustomCampaign({
        subject: response.data.campaign.subject,
        message: response.data.campaign.message,
        promo_code: response.data.campaign.promo_code,
        discount: response.data.campaign.discount
      });
      setCampaignDialog(segment);
    } catch (error) {
      toast.error("Failed to generate campaign");
    }
  };

  const sendCampaign = async () => {
    setSendingCampaign(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/customer-segments/${campaignDialog}/send-campaign`,
        customCampaign,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(response.data.message);
      setCampaignDialog(null);
    } catch (error) {
      toast.error("Failed to send campaign");
    } finally {
      setSendingCampaign(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value);
  };

  const getSegmentIcon = (segment) => {
    const Icon = SEGMENT_ICONS[segment] || Users;
    return Icon;
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12 bg-[#FDF8F3]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-64"></div>
            <div className="grid grid-cols-3 gap-6">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-48 bg-gray-200 rounded-2xl"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-12 bg-[#FDF8F3]">
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
                Customer Segments
              </h1>
              <p className="text-[#5C6D5E]">AI-powered customer segmentation for targeted campaigns</p>
            </div>
          </div>
          <Badge className="bg-[#6B8F71] text-white px-4 py-2">
            <Zap className="w-4 h-4 mr-2" />
            Auto-Updated
          </Badge>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#2D4A3E] rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-3xl font-bold text-[#2D4A3E]">{summary.total_customers || 0}</p>
                <p className="text-sm text-[#5C6D5E]">Total Customers</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#6B8F71] rounded-xl flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-3xl font-bold text-[#2D4A3E]">{formatCurrency(summary.total_revenue || 0)}</p>
                <p className="text-sm text-[#5C6D5E]">Total Revenue</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#D4A574] rounded-xl flex items-center justify-center">
                <ShoppingBag className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-3xl font-bold text-[#2D4A3E]">{summary.segment_count || 0}</p>
                <p className="text-sm text-[#5C6D5E]">Active Segments</p>
              </div>
            </div>
          </div>
        </div>

        {/* Segment Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {segments.map((segment) => {
            const Icon = getSegmentIcon(segment.segment);
            return (
              <div 
                key={segment.segment} 
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow"
                data-testid={`segment-${segment.segment}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: `${segment.color}20` }}
                  >
                    <Icon className="w-6 h-6" style={{ color: segment.color }} />
                  </div>
                  <Badge 
                    className="text-white"
                    style={{ backgroundColor: segment.color }}
                  >
                    {segment.customer_count} customers
                  </Badge>
                </div>
                
                <h3 className="text-lg font-semibold text-[#2D4A3E] mb-1">{segment.label}</h3>
                <p className="text-sm text-[#5C6D5E] mb-4">{segment.description}</p>
                
                <div className="bg-[#FDF8F3] rounded-xl p-4 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[#5C6D5E]">Total Revenue</span>
                    <span className="font-semibold text-[#2D4A3E]">{formatCurrency(segment.total_revenue)}</span>
                  </div>
                </div>
                
                {/* Preview Customers */}
                {segment.customers && segment.customers.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-[#5C6D5E] mb-2">Recent customers:</p>
                    <div className="flex -space-x-2">
                      {segment.customers.slice(0, 5).map((customer, idx) => (
                        <div 
                          key={customer.id || idx}
                          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium border-2 border-white"
                          style={{ backgroundColor: segment.color }}
                          title={customer.email}
                        >
                          {customer.name?.charAt(0).toUpperCase() || customer.email?.charAt(0).toUpperCase() || "?"}
                        </div>
                      ))}
                      {segment.customer_count > 5 && (
                        <div className="w-8 h-8 rounded-full bg-[#E8DFD5] flex items-center justify-center text-xs font-medium text-[#2D4A3E] border-2 border-white">
                          +{segment.customer_count - 5}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1 rounded-full text-sm"
                    onClick={() => setSelectedSegment(segment)}
                    data-testid={`view-${segment.segment}`}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    View
                  </Button>
                  <Button
                    className="flex-1 rounded-full text-sm"
                    style={{ backgroundColor: segment.color }}
                    onClick={() => generateCampaign(segment.segment)}
                    data-testid={`campaign-${segment.segment}`}
                  >
                    <Mail className="w-4 h-4 mr-1" />
                    Campaign
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {segments.length === 0 && (
          <div className="bg-white rounded-2xl p-12 text-center">
            <Users className="w-12 h-12 text-[#5C6D5E] mx-auto mb-4" />
            <p className="text-[#5C6D5E]">No customer segments found. Segments are created automatically based on purchase behavior.</p>
          </div>
        )}

        {/* View Segment Dialog */}
        <Dialog open={!!selectedSegment} onOpenChange={() => setSelectedSegment(null)}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E] font-['Fraunces'] flex items-center gap-2">
                {selectedSegment && (() => {
                  const Icon = getSegmentIcon(selectedSegment.segment);
                  return <Icon className="w-5 h-5" style={{ color: selectedSegment.color }} />;
                })()}
                {selectedSegment?.label}
              </DialogTitle>
              <DialogDescription>{selectedSegment?.description}</DialogDescription>
            </DialogHeader>
            
            {selectedSegment && (
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#FDF8F3] rounded-xl p-4">
                    <p className="text-2xl font-bold text-[#2D4A3E]">{selectedSegment.customer_count}</p>
                    <p className="text-sm text-[#5C6D5E]">Customers</p>
                  </div>
                  <div className="bg-[#FDF8F3] rounded-xl p-4">
                    <p className="text-2xl font-bold text-[#2D4A3E]">{formatCurrency(selectedSegment.total_revenue)}</p>
                    <p className="text-sm text-[#5C6D5E]">Total Revenue</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-[#2D4A3E] mb-3">Customers in this segment</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {selectedSegment.customers?.map((customer) => (
                      <div key={customer.id} className="flex items-center justify-between p-3 bg-white border border-[#E8DFD5] rounded-lg">
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-medium"
                            style={{ backgroundColor: selectedSegment.color }}
                          >
                            {customer.name?.charAt(0).toUpperCase() || customer.email?.charAt(0).toUpperCase() || "?"}
                          </div>
                          <div>
                            <p className="font-medium text-[#2D4A3E]">{customer.name || "Unknown"}</p>
                            <p className="text-sm text-[#5C6D5E]">{customer.email}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-[#2D4A3E]">{formatCurrency(customer.total_spend)}</p>
                          <p className="text-xs text-[#5C6D5E]">{customer.total_orders} orders</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedSegment(null)} className="rounded-full">
                Close
              </Button>
              <Button 
                onClick={() => {
                  setSelectedSegment(null);
                  generateCampaign(selectedSegment.segment);
                }}
                className="rounded-full"
                style={{ backgroundColor: selectedSegment?.color }}
              >
                <Mail className="w-4 h-4 mr-2" />
                Create Campaign
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Campaign Dialog */}
        <Dialog open={!!campaignDialog} onOpenChange={() => setCampaignDialog(null)}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-[#2D4A3E] font-['Fraunces']">
                Create Campaign for {campaignData?.label}
              </DialogTitle>
              <DialogDescription>
                Send a targeted email to {campaignData?.customer_count} customers
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Email Subject</Label>
                <Input
                  value={customCampaign.subject}
                  onChange={(e) => setCustomCampaign(prev => ({ ...prev, subject: e.target.value }))}
                  className="rounded-lg"
                  data-testid="campaign-subject"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Message</Label>
                <Textarea
                  value={customCampaign.message}
                  onChange={(e) => setCustomCampaign(prev => ({ ...prev, message: e.target.value }))}
                  rows={3}
                  className="rounded-lg"
                  data-testid="campaign-message"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Discount Offer</Label>
                  <Input
                    value={customCampaign.discount}
                    onChange={(e) => setCustomCampaign(prev => ({ ...prev, discount: e.target.value }))}
                    placeholder="e.g., 20% off"
                    className="rounded-lg"
                    data-testid="campaign-discount"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Promo Code</Label>
                  <Input
                    value={customCampaign.promo_code}
                    onChange={(e) => setCustomCampaign(prev => ({ ...prev, promo_code: e.target.value }))}
                    placeholder="e.g., VIP20"
                    className="rounded-lg"
                    data-testid="campaign-code"
                  />
                </div>
              </div>
              
              {/* Preview */}
              {campaignData?.campaign?.preview_html && (
                <div className="space-y-2">
                  <Label>Email Preview</Label>
                  <div 
                    className="border border-[#E8DFD5] rounded-xl overflow-hidden"
                    dangerouslySetInnerHTML={{ __html: campaignData.campaign.preview_html }}
                  />
                </div>
              )}
            </div>
            
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setCampaignDialog(null)} className="rounded-full">
                Cancel
              </Button>
              <Button 
                onClick={sendCampaign}
                disabled={sendingCampaign}
                className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
                data-testid="send-campaign-btn"
              >
                {sendingCampaign ? (
                  "Sending..."
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Send to {campaignData?.customer_count} Customers
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminCustomerSegmentsPage;
