import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { 
  Search, 
  TrendingUp, 
  Shield, 
  Package, 
  Sparkles, 
  ArrowRight,
  CheckCircle2,
  Heart,
  Dog
} from "lucide-react";
import AuthModal from "../components/AuthModal";

const LandingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showAuth, setShowAuth] = useState(false);

  const features = [
    {
      icon: <Search className="w-6 h-6" />,
      title: "AI-Powered Research",
      description: "Claude Opus 4.6 analyzes products against 7 key criteria to find winning pet wellness items."
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Demand Validation",
      description: "Real-time trend analysis from TikTok, Pinterest, and Google Trends to verify market demand."
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Supplier Verification",
      description: "Only vetted suppliers from CJdropshipping US warehouse, Zendrop, and Spocket."
    },
    {
      icon: <Package className="w-6 h-6" />,
      title: "Margin Calculator",
      description: "Automatic 65%+ gross margin targeting with full landed cost breakdown."
    }
  ];

  const stats = [
    { number: "65%+", label: "Target Margin" },
    { number: "4.5★", label: "Min Supplier Rating" },
    { number: "$28-99", label: "Price Range" },
    { number: "3 Days", label: "Max Processing" }
  ];

  const handleGetStarted = () => {
    if (user) {
      navigate("/research");
    } else {
      setShowAuth(true);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-32">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center gap-2 bg-[#768A75]/10 text-[#768A75] px-4 py-2 rounded-full text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                <span>AI-Powered Product Sourcing</span>
              </div>
              
              <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-none text-[#2F3E32] mb-6 font-['Fraunces']">
                Find Winning Pet Wellness Products
              </h1>
              
              <p className="text-lg md:text-xl leading-relaxed text-[#57534E] mb-8 max-w-xl">
                Your AI sourcing agent for premium pet wellness dropshipping. 
                Verified suppliers, margin analysis, and trend validation — all in one place.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <button
                  onClick={handleGetStarted}
                  className="bg-[#2F3E32] text-white px-8 py-4 rounded-full font-medium hover:bg-[#253229] transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 inline-flex items-center justify-center gap-2"
                  data-testid="hero-get-started-btn"
                >
                  Start Sourcing Free
                  <ArrowRight className="w-5 h-5" />
                </button>
                <Link
                  to="/research"
                  className="bg-white border border-stone-200 text-stone-800 hover:bg-stone-50 rounded-full px-8 py-4 font-medium transition-all text-center"
                  data-testid="hero-try-demo-btn"
                >
                  Try Demo
                </Link>
              </div>
              
              {!user && (
                <div className="discount-badge inline-flex">
                  <Heart className="w-4 h-4" />
                  <span>Sign up for 15% off your first month</span>
                </div>
              )}
            </div>
            
            {/* Right Image */}
            <div className="relative animate-fade-in stagger-2">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1768676758480-44e11e5c164a"
                  alt="Golden retriever in golden hour sunlight"
                  className="w-full h-[500px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#2F3E32]/30 to-transparent"></div>
              </div>
              
              {/* Floating Card */}
              <div className="absolute -bottom-6 -left-6 bg-white rounded-2xl shadow-xl p-4 animate-fade-in-up stagger-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#768A75] flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#2F3E32] text-sm">Verified Supplier</p>
                    <p className="text-xs text-[#57534E]">US Warehouse • 4.8★ Rating</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-[#F2F0E9] py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div 
                key={index} 
                className="stat-card animate-fade-in-up"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="stat-number">{stat.number}</div>
                <div className="stat-label">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="section-header">How It Works</p>
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-[#2F3E32] font-['Fraunces']">
              Intelligent Product Sourcing
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="card-base p-6 animate-fade-in-up"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="feature-icon mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-[#2F3E32] mb-2 font-['Fraunces']">
                  {feature.title}
                </h3>
                <p className="text-[#57534E] text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Suppliers Section */}
      <section className="py-24 bg-[#F2F0E9]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="section-header">Trusted Sources</p>
              <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-[#2F3E32] mb-6 font-['Fraunces']">
                Vetted Supplier Network
              </h2>
              <p className="text-lg text-[#57534E] mb-8 leading-relaxed">
                We only source from verified platforms with US warehouse capabilities, 
                ensuring fast shipping and reliable fulfillment for your customers.
              </p>
              
              <div className="space-y-4">
                {[
                  "CJdropshipping US Warehouse",
                  "Zendrop Verified Partners",
                  "Spocket Premium Suppliers",
                  "Faire Wholesale Brands"
                ].map((supplier, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#768A75]" />
                    <span className="text-[#2F3E32] font-medium">{supplier}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1673573032549-8394cf9282f3"
                alt="Eco packaging boxes"
                className="rounded-3xl shadow-2xl w-full h-[400px] object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-[#2F3E32] rounded-3xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <Dog className="w-96 h-96 absolute -right-16 -bottom-16" />
            </div>
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 font-['Fraunces']">
                Ready to Find Your Next Bestseller?
              </h2>
              <p className="text-[#F2F0E9]/80 text-lg mb-8 max-w-xl mx-auto">
                Join dropshippers who use AI to source premium pet wellness products 
                with verified margins and demand signals.
              </p>
              <button
                onClick={handleGetStarted}
                className="bg-[#D4A373] text-[#2F3E32] px-8 py-4 rounded-full font-semibold hover:bg-[#C89565] transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 inline-flex items-center gap-2"
                data-testid="cta-get-started-btn"
              >
                Start Sourcing Now
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#F2F0E9] py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-[#2F3E32] rounded-lg flex items-center justify-center">
                <Dog className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-[#2F3E32] font-['Fraunces']">PetPulse</span>
            </div>
            <p className="text-sm text-[#57534E]">
              © 2026 PetPulse Sourcing. Premium pet wellness product research.
            </p>
          </div>
        </div>
      </footer>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
};

export default LandingPage;
