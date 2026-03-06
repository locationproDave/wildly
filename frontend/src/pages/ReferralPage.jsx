import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../App";
import { toast } from "sonner";
import { 
  Gift, 
  Copy, 
  Share2, 
  CheckCircle, 
  Users,
  DollarSign,
  ChevronLeft,
  Twitter,
  Facebook,
  Mail
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ReferralPage = () => {
  const { token, user } = useAuth();
  const [referralData, setReferralData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (token) {
      fetchReferralData();
    }
  }, [token]);

  const fetchReferralData = async () => {
    try {
      const [codeRes, statsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/referral/code`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/referral/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setReferralData(codeRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching referral data:", error);
      toast.error("Failed to load referral data");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(referralData.share_url);
      setCopied(true);
      toast.success("Link copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };

  const shareOnTwitter = () => {
    const text = `Get $10 off your first order at Wildly Ones Pet Wellness! Use my link:`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(referralData.share_url)}`, '_blank');
  };

  const shareOnFacebook = () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(referralData.share_url)}`, '_blank');
  };

  const shareByEmail = () => {
    const subject = "Get $10 off at Wildly Ones Pet Wellness!";
    const body = `Hey! I thought you'd love Wildly Ones - they have amazing pet wellness products. Use my referral link to get $10 off your first order: ${referralData.share_url}`;
    window.open(`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
  };

  if (!token) {
    return (
      <div className="min-h-screen pt-24 pb-12 flex items-center justify-center">
        <div className="text-center max-w-md">
          <Gift className="w-16 h-16 text-[#D4A574] mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-[#2D4A3E] mb-4 font-['Fraunces']">
            Give $10, Get $10
          </h2>
          <p className="text-[#5C6D5E] mb-6">
            Sign in to get your personal referral link and start earning rewards!
          </p>
          <Link to="/account">
            <Button className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full">
              Sign In to Continue
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24 pb-12">
        <div className="max-w-4xl mx-auto px-4 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-8"></div>
          <div className="h-48 bg-gray-200 rounded-2xl mb-8"></div>
          <div className="h-32 bg-gray-200 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link 
          to="/account" 
          className="inline-flex items-center text-[#5C6D5E] hover:text-[#2D4A3E] mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Account
        </Link>

        {/* Hero Section */}
        <div className="bg-gradient-to-br from-[#2D4A3E] to-[#3D5A4E] rounded-3xl p-8 md:p-12 mb-8 text-white">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-[#D4A574] rounded-2xl flex items-center justify-center">
              <Gift className="w-8 h-8 text-[#2D4A3E]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold font-['Fraunces']">Give $10, Get $10</h1>
              <p className="text-white/80">Share the love for happy, calm pets</p>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold mb-2">How it works:</h3>
              <ol className="space-y-2 text-white/90">
                <li className="flex items-start gap-2">
                  <span className="w-6 h-6 rounded-full bg-[#D4A574] text-[#2D4A3E] flex items-center justify-center text-sm font-bold shrink-0">1</span>
                  <span>Share your unique referral link with friends</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-6 h-6 rounded-full bg-[#D4A574] text-[#2D4A3E] flex items-center justify-center text-sm font-bold shrink-0">2</span>
                  <span>They get $10 off their first order</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-6 h-6 rounded-full bg-[#D4A574] text-[#2D4A3E] flex items-center justify-center text-sm font-bold shrink-0">3</span>
                  <span>You get $10 off + 100 bonus points when they buy!</span>
                </li>
              </ol>
            </div>
            
            <div className="bg-white/10 rounded-2xl p-6">
              <p className="text-sm text-white/70 mb-2">Your Referral Code</p>
              <p className="text-2xl font-bold font-mono mb-4" data-testid="referral-code">
                {referralData?.referral_code}
              </p>
              <div className="flex gap-2">
                <Input
                  value={referralData?.share_url || ""}
                  readOnly
                  className="bg-white/20 border-white/30 text-white placeholder:text-white/50"
                />
                <Button
                  onClick={copyToClipboard}
                  variant="secondary"
                  className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] shrink-0"
                  data-testid="copy-link-btn"
                >
                  {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Share Buttons */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-8">
          <h2 className="font-semibold text-[#2D4A3E] mb-4 flex items-center gap-2">
            <Share2 className="w-5 h-5" />
            Share Your Link
          </h2>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={shareOnTwitter}
              variant="outline"
              className="rounded-full"
            >
              <Twitter className="w-4 h-4 mr-2" />
              Twitter
            </Button>
            <Button
              onClick={shareOnFacebook}
              variant="outline"
              className="rounded-full"
            >
              <Facebook className="w-4 h-4 mr-2" />
              Facebook
            </Button>
            <Button
              onClick={shareByEmail}
              variant="outline"
              className="rounded-full"
            >
              <Mail className="w-4 h-4 mr-2" />
              Email
            </Button>
            <Button
              onClick={copyToClipboard}
              variant="outline"
              className="rounded-full"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy Link
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
            <Users className="w-8 h-8 text-[#6B8F71] mx-auto mb-3" />
            <p className="text-3xl font-bold text-[#2D4A3E]">{stats?.total_referrals || 0}</p>
            <p className="text-sm text-[#5C6D5E]">Friends Referred</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
            <DollarSign className="w-8 h-8 text-[#D4A574] mx-auto mb-3" />
            <p className="text-3xl font-bold text-[#2D4A3E]">${stats?.total_earned || 0}</p>
            <p className="text-sm text-[#5C6D5E]">Total Earned</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
            <Gift className="w-8 h-8 text-[#7CA5B8] mx-auto mb-3" />
            <p className="text-3xl font-bold text-[#2D4A3E]">{stats?.pending_referrals || 0}</p>
            <p className="text-sm text-[#5C6D5E]">Pending Referrals</p>
          </div>
        </div>

        {/* Referral History */}
        {stats?.referrals && stats.referrals.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-[#E8DFD5]">
              <h2 className="font-semibold text-[#2D4A3E]">Referral History</h2>
            </div>
            <div className="divide-y divide-[#E8DFD5]">
              {stats.referrals.map((referral, idx) => (
                <div key={idx} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-[#2D4A3E]">{referral.referee_email}</p>
                    <p className="text-sm text-[#5C6D5E]">
                      {referral.status === "completed" 
                        ? `Completed ${new Date(referral.completed_at).toLocaleDateString()}`
                        : "Pending - waiting for first order"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${referral.status === "completed" ? "text-[#6B8F71]" : "text-[#D4A574]"}`}>
                      {referral.status === "completed" ? `+$${referral.reward}` : "Pending"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReferralPage;
