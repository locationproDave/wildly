import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { 
  Mail, 
  Phone, 
  MessageCircle, 
  Truck, 
  RotateCcw, 
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  MapPin,
  Send
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { toast } from "sonner";

const SupportPage = () => {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("contact");
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [contactForm, setContactForm] = useState({
    name: "",
    email: "",
    subject: "",
    message: ""
  });

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab && ["contact", "shipping", "returns", "faq"].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tabId) => {
    if (tabId !== activeTab) {
      setActiveTab(tabId);
      window.scrollTo(0, 0);
    }
  };

  const tabs = [
    { id: "contact", label: "Contact Us", icon: Mail },
    { id: "shipping", label: "Shipping Info", icon: Truck },
    { id: "returns", label: "Returns & Refunds", icon: RotateCcw },
    { id: "faq", label: "FAQ", icon: HelpCircle },
  ];

  const faqData = [
    {
      category: "Orders & Shipping",
      questions: [
        {
          q: "How long does shipping take?",
          a: "Standard shipping takes 3-5 business days within the US. Express shipping (1-2 business days) is available at checkout for an additional fee. International shipping typically takes 7-14 business days."
        },
        {
          q: "How can I track my order?",
          a: "Once your order ships, you'll receive a confirmation email with a tracking number. You can also track your order by logging into your account and viewing your order history."
        },
        {
          q: "Do you offer free shipping?",
          a: "Yes! We offer free standard shipping on all orders over $50 within the continental US."
        },
        {
          q: "Can I change or cancel my order?",
          a: "You can modify or cancel your order within 1 hour of placing it. After that, please contact our support team and we'll do our best to accommodate your request before the order ships."
        }
      ]
    },
    {
      category: "Returns & Refunds",
      questions: [
        {
          q: "What is your return policy?",
          a: "We offer a 30-day return policy for unopened items in original packaging. If you're not satisfied with your purchase, contact us for a return authorization."
        },
        {
          q: "How do I initiate a return?",
          a: "To start a return, email us at returns@wildlyones.com with your order number and reason for return. We'll send you a prepaid return label within 24 hours."
        },
        {
          q: "When will I receive my refund?",
          a: "Refunds are processed within 5-7 business days after we receive your return. The refund will be credited to your original payment method."
        },
        {
          q: "Can I exchange an item?",
          a: "Yes! We offer free exchanges for different sizes or products of equal value. Contact us to arrange an exchange."
        }
      ]
    },
    {
      category: "Products & Subscriptions",
      questions: [
        {
          q: "Are your products safe for my pet?",
          a: "Absolutely! All our products are vet-reviewed and made with natural, pet-safe ingredients. We never use harmful chemicals or artificial additives."
        },
        {
          q: "How does the subscription work?",
          a: "Subscribe & Save gives you 10% off every order with automatic monthly deliveries. You can pause, skip, or cancel anytime from your account page."
        },
        {
          q: "Can I customize my subscription?",
          a: "Yes! You can change products, quantities, and delivery frequency at any time through your account dashboard."
        },
        {
          q: "What if my pet doesn't like a product?",
          a: "We want your pet to be happy! If your pet doesn't take to a product, contact us within 30 days for a full refund or exchange."
        }
      ]
    },
    {
      category: "Account & Rewards",
      questions: [
        {
          q: "How do I earn reward points?",
          a: "Earn 1 point for every $1 spent. Points can be redeemed for discounts on future purchases. 100 points = $5 off!"
        },
        {
          q: "How does the referral program work?",
          a: "Share your unique referral code with friends. When they make their first purchase, they get 15% off and you earn $10 in store credit!"
        },
        {
          q: "I forgot my password. What do I do?",
          a: "Click 'Sign In' and then 'Forgot Password' to receive a reset link via email. If you don't receive it, check your spam folder or contact support."
        }
      ]
    }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      toast.error("Please fill in all required fields");
      return;
    }
    toast.success("Message sent! We'll get back to you within 24 hours.");
    setContactForm({ name: "", email: "", subject: "", message: "" });
  };

  const toggleFaq = (index) => {
    setExpandedFaq(expandedFaq === index ? null : index);
  };

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#2D4A3E] mb-2 font-['Fraunces']">
            How Can We Help?
          </h1>
          <p className="text-[#5C6D5E]">
            We're here to make sure you and your pet are happy
          </p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? "bg-[#2D4A3E] text-white"
                    : "bg-white text-[#2D4A3E] hover:bg-[#E8DFD5]"
                }`}
                data-testid={`support-tab-${tab.id}`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Contact Us Tab */}
        {activeTab === "contact" && (
          <div className="grid md:grid-cols-2 gap-8">
            {/* Contact Form */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
                Send Us a Message
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="name" className="text-[#2D4A3E]">Name *</Label>
                  <Input
                    id="name"
                    value={contactForm.name}
                    onChange={(e) => setContactForm({...contactForm, name: e.target.value})}
                    placeholder="Your name"
                    className="mt-1 rounded-xl"
                  />
                </div>
                <div>
                  <Label htmlFor="email" className="text-[#2D4A3E]">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={contactForm.email}
                    onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                    placeholder="your@email.com"
                    className="mt-1 rounded-xl"
                  />
                </div>
                <div>
                  <Label htmlFor="subject" className="text-[#2D4A3E]">Subject</Label>
                  <Input
                    id="subject"
                    value={contactForm.subject}
                    onChange={(e) => setContactForm({...contactForm, subject: e.target.value})}
                    placeholder="What's this about?"
                    className="mt-1 rounded-xl"
                  />
                </div>
                <div>
                  <Label htmlFor="message" className="text-[#2D4A3E]">Message *</Label>
                  <textarea
                    id="message"
                    value={contactForm.message}
                    onChange={(e) => setContactForm({...contactForm, message: e.target.value})}
                    placeholder="How can we help?"
                    rows={4}
                    className="mt-1 w-full rounded-xl border border-[#E8DFD5] p-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D4A3E]/20"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full rounded-full bg-[#2D4A3E] hover:bg-[#1F342B]"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send Message
                </Button>
              </form>
            </div>

            {/* Contact Info */}
            <div className="space-y-4">
              <div className="bg-white rounded-2xl p-6 shadow-sm">
                <h3 className="font-semibold text-[#2D4A3E] mb-4">Other Ways to Reach Us</h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-[#6B8F71]/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Mail className="w-5 h-5 text-[#6B8F71]" />
                    </div>
                    <div>
                      <p className="font-medium text-[#2D4A3E]">Email</p>
                      <p className="text-sm text-[#5C6D5E]">support@wildlyones.com</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-[#D4A574]/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Phone className="w-5 h-5 text-[#D4A574]" />
                    </div>
                    <div>
                      <p className="font-medium text-[#2D4A3E]">Phone</p>
                      <p className="text-sm text-[#5C6D5E]">1-800-WILDLY-1 (1-800-945-3591)</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-[#C45C4A]/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <MessageCircle className="w-5 h-5 text-[#C45C4A]" />
                    </div>
                    <div>
                      <p className="font-medium text-[#2D4A3E]">Live Chat</p>
                      <p className="text-sm text-[#5C6D5E]">Available Mon-Fri, 9am-6pm EST</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#2D4A3E] rounded-2xl p-6 text-white">
                <div className="flex items-center gap-3 mb-3">
                  <Clock className="w-5 h-5 text-[#D4A574]" />
                  <h3 className="font-semibold">Response Times</h3>
                </div>
                <ul className="space-y-2 text-sm text-white/80">
                  <li>Email: Within 24 hours</li>
                  <li>Phone: Immediate during business hours</li>
                  <li>Live Chat: Usually under 5 minutes</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Shipping Info Tab */}
        {activeTab === "shipping" && (
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h2 className="text-xl font-bold text-[#2D4A3E] mb-6 font-['Fraunces']">
              Shipping Information
            </h2>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="text-center p-4 bg-[#E8DFD5]/30 rounded-xl">
                <div className="w-12 h-12 bg-[#6B8F71] rounded-full flex items-center justify-center mx-auto mb-3">
                  <Truck className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold text-[#2D4A3E] mb-1">Standard Shipping</h3>
                <p className="text-2xl font-bold text-[#6B8F71]">FREE</p>
                <p className="text-sm text-[#5C6D5E]">Orders over $50</p>
                <p className="text-xs text-[#5C6D5E] mt-1">3-5 business days</p>
              </div>
              <div className="text-center p-4 bg-[#E8DFD5]/30 rounded-xl">
                <div className="w-12 h-12 bg-[#D4A574] rounded-full flex items-center justify-center mx-auto mb-3">
                  <Truck className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold text-[#2D4A3E] mb-1">Express Shipping</h3>
                <p className="text-2xl font-bold text-[#D4A574]">$9.99</p>
                <p className="text-sm text-[#5C6D5E]">All orders</p>
                <p className="text-xs text-[#5C6D5E] mt-1">1-2 business days</p>
              </div>
              <div className="text-center p-4 bg-[#E8DFD5]/30 rounded-xl">
                <div className="w-12 h-12 bg-[#2D4A3E] rounded-full flex items-center justify-center mx-auto mb-3">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold text-[#2D4A3E] mb-1">International</h3>
                <p className="text-2xl font-bold text-[#2D4A3E]">$14.99</p>
                <p className="text-sm text-[#5C6D5E]">Select countries</p>
                <p className="text-xs text-[#5C6D5E] mt-1">7-14 business days</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="border-l-4 border-[#6B8F71] pl-4">
                <h3 className="font-semibold text-[#2D4A3E]">Order Processing</h3>
                <p className="text-sm text-[#5C6D5E]">Orders placed before 2pm EST Monday-Friday are processed the same day. Weekend orders are processed the next business day.</p>
              </div>
              <div className="border-l-4 border-[#D4A574] pl-4">
                <h3 className="font-semibold text-[#2D4A3E]">Tracking Your Order</h3>
                <p className="text-sm text-[#5C6D5E]">You'll receive a shipping confirmation email with tracking information once your order ships. You can also track orders in your account.</p>
              </div>
              <div className="border-l-4 border-[#2D4A3E] pl-4">
                <h3 className="font-semibold text-[#2D4A3E]">Shipping Carriers</h3>
                <p className="text-sm text-[#5C6D5E]">We ship via UPS, FedEx, and USPS depending on your location and shipping speed selected. All packages include tracking.</p>
              </div>
            </div>
          </div>
        )}

        {/* Returns & Refunds Tab */}
        {activeTab === "returns" && (
          <div className="bg-white rounded-2xl p-6 shadow-sm">
            <h2 className="text-xl font-bold text-[#2D4A3E] mb-6 font-['Fraunces']">
              Returns & Refunds Policy
            </h2>

            <div className="bg-[#6B8F71]/10 rounded-xl p-4 mb-6">
              <div className="flex items-center gap-3">
                <RotateCcw className="w-6 h-6 text-[#6B8F71]" />
                <div>
                  <h3 className="font-semibold text-[#2D4A3E]">30-Day Happiness Guarantee</h3>
                  <p className="text-sm text-[#5C6D5E]">Not satisfied? Return any unopened item within 30 days for a full refund.</p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-[#2D4A3E] mb-2">Eligible Returns</h3>
                <ul className="space-y-2 text-sm text-[#5C6D5E]">
                  <li className="flex items-start gap-2">
                    <span className="text-[#6B8F71]">✓</span>
                    Unopened items in original packaging
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#6B8F71]">✓</span>
                    Items returned within 30 days of delivery
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#6B8F71]">✓</span>
                    Defective or damaged products (contact us immediately)
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#6B8F71]">✓</span>
                    Wrong item received
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-[#2D4A3E] mb-2">Non-Returnable Items</h3>
                <ul className="space-y-2 text-sm text-[#5C6D5E]">
                  <li className="flex items-start gap-2">
                    <span className="text-[#C45C4A]">✗</span>
                    Opened food, treats, or supplements
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#C45C4A]">✗</span>
                    Personalized or custom items
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-[#C45C4A]">✗</span>
                    Items marked as final sale
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-[#2D4A3E] mb-2">How to Return</h3>
                <ol className="space-y-2 text-sm text-[#5C6D5E]">
                  <li><span className="font-medium text-[#2D4A3E]">1.</span> Email returns@wildlyones.com with your order number</li>
                  <li><span className="font-medium text-[#2D4A3E]">2.</span> Receive your prepaid return label within 24 hours</li>
                  <li><span className="font-medium text-[#2D4A3E]">3.</span> Pack items securely in original packaging</li>
                  <li><span className="font-medium text-[#2D4A3E]">4.</span> Drop off at any UPS location</li>
                  <li><span className="font-medium text-[#2D4A3E]">5.</span> Refund processed within 5-7 business days of receipt</li>
                </ol>
              </div>

              <div className="bg-[#D4A574]/10 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D4A3E] mb-1">Pet Didn't Like It?</h3>
                <p className="text-sm text-[#5C6D5E]">We understand pets can be picky! If your furry friend doesn't take to a product, contact us within 30 days. We'll work with you to find a solution - whether that's an exchange, store credit, or refund.</p>
              </div>
            </div>
          </div>
        )}

        {/* FAQ Tab */}
        {activeTab === "faq" && (
          <div className="space-y-6">
            {faqData.map((section, sectionIndex) => (
              <div key={section.category} className="bg-white rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
                  {section.category}
                </h2>
                <div className="space-y-2">
                  {section.questions.map((item, itemIndex) => {
                    const index = `${sectionIndex}-${itemIndex}`;
                    const isExpanded = expandedFaq === index;
                    return (
                      <div key={index} className="border-b border-[#E8DFD5] last:border-0">
                        <button
                          onClick={() => toggleFaq(index)}
                          className="w-full flex items-center justify-between py-3 text-left"
                          data-testid={`faq-${index}`}
                        >
                          <span className="font-medium text-[#2D4A3E] pr-4">{item.q}</span>
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-[#5C6D5E] flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-[#5C6D5E] flex-shrink-0" />
                          )}
                        </button>
                        {isExpanded && (
                          <div className="pb-3 text-sm text-[#5C6D5E]">
                            {item.a}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Still Need Help Banner */}
        <div className="mt-8 bg-gradient-to-r from-[#2D4A3E] to-[#3D5A4E] rounded-2xl p-6 text-center text-white">
          <h3 className="text-xl font-bold font-['Fraunces'] mb-2">Still Need Help?</h3>
          <p className="text-white/80 mb-4">Our pet-loving support team is here for you</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button 
              onClick={() => handleTabChange("contact")}
              className="bg-white text-[#2D4A3E] hover:bg-[#E8DFD5] rounded-full"
            >
              <Mail className="w-4 h-4 mr-2" />
              Contact Us
            </Button>
            <Button 
              variant="outline" 
              className="border-white text-white hover:bg-white/10 rounded-full"
            >
              <Phone className="w-4 h-4 mr-2" />
              1-800-WILDLY-1
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupportPage;
