import React from "react";
import { Link } from "react-router-dom";
import { 
  Mail, 
  Instagram, 
  Facebook,
  Twitter
} from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-[#2D4A3E] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🐾</span>
              <span className="font-bold text-xl font-['Fraunces']">Wildly Ones</span>
            </div>
            <p className="text-white/70 text-sm leading-relaxed">
              Premium pet wellness products designed with science and love. 
              Because every tail deserves to wag.
            </p>
          </div>

          {/* Shop */}
          <div>
            <h3 className="font-semibold mb-4">Shop</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/products" className="text-white/70 hover:text-white text-sm transition-colors">
                  All Products
                </Link>
              </li>
              <li>
                <Link to="/products?pet_type=dog" className="text-white/70 hover:text-white text-sm transition-colors">
                  For Dogs
                </Link>
              </li>
              <li>
                <Link to="/products?pet_type=cat" className="text-white/70 hover:text-white text-sm transition-colors">
                  For Cats
                </Link>
              </li>
              <li>
                <Link to="/products?category=Supplements" className="text-white/70 hover:text-white text-sm transition-colors">
                  Supplements
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold mb-4">Support</h3>
            <ul className="space-y-2">
              <li>
                <span className="text-white/70 text-sm">Contact Us</span>
              </li>
              <li>
                <span className="text-white/70 text-sm">Shipping Info</span>
              </li>
              <li>
                <span className="text-white/70 text-sm">Returns & Refunds</span>
              </li>
              <li>
                <span className="text-white/70 text-sm">FAQ</span>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h3 className="font-semibold mb-4">Connect</h3>
            <div className="flex gap-4 mb-4">
              <a href="#" className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 transition-colors">
                <Instagram className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 transition-colors">
                <Facebook className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center hover:bg-white/20 transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
            </div>
            <div className="flex items-center gap-2 text-white/70">
              <Mail className="w-4 h-4" />
              <span className="text-sm">hello@wildlyones.com</span>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-white/50 text-sm">
            © 2026 Wildly Ones. All rights reserved.
          </p>
          <div className="flex gap-6">
            <span className="text-white/50 text-sm">Privacy Policy</span>
            <span className="text-white/50 text-sm">Terms of Service</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
