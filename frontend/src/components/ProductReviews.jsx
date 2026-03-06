import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../App";
import { toast } from "sonner";
import { 
  Star, 
  ThumbsUp, 
  CheckCircle, 
  User,
  ChevronDown,
  ChevronUp,
  Award
} from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { Progress } from "./ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const StarRating = ({ rating, onRate, interactive = false, size = "md" }) => {
  const [hovered, setHovered] = useState(0);
  const starSize = size === "sm" ? "w-4 h-4" : size === "lg" ? "w-8 h-8" : "w-5 h-5";
  
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => interactive && onRate && onRate(star)}
          onMouseEnter={() => interactive && setHovered(star)}
          onMouseLeave={() => interactive && setHovered(0)}
          className={`${interactive ? "cursor-pointer" : "cursor-default"}`}
          disabled={!interactive}
        >
          <Star
            className={`${starSize} ${
              (hovered || rating) >= star
                ? "fill-[#D4A574] text-[#D4A574]"
                : "text-[#E8DFD5]"
            } transition-colors`}
          />
        </button>
      ))}
    </div>
  );
};

const ReviewCard = ({ review, onHelpful }) => {
  const [helpfulClicked, setHelpfulClicked] = useState(false);
  
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { 
      year: "numeric", 
      month: "long", 
      day: "numeric" 
    });
  };
  
  const handleHelpful = async () => {
    if (helpfulClicked) return;
    setHelpfulClicked(true);
    await onHelpful(review.id);
  };
  
  return (
    <div className="border-b border-[#E8DFD5] py-6 last:border-0" data-testid={`review-${review.id}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#E8DFD5] flex items-center justify-center">
            <User className="w-5 h-5 text-[#5C6D5E]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[#2D4A3E]">{review.user_name}</span>
              {review.verified_purchase && (
                <span className="flex items-center gap-1 text-xs text-[#6B8F71] bg-[#6B8F71]/10 px-2 py-0.5 rounded-full">
                  <CheckCircle className="w-3 h-3" />
                  Verified Purchase
                </span>
              )}
            </div>
            <span className="text-sm text-[#5C6D5E]">{formatDate(review.created_at)}</span>
          </div>
        </div>
        <StarRating rating={review.rating} size="sm" />
      </div>
      
      <h4 className="font-semibold text-[#2D4A3E] mb-2">{review.title}</h4>
      <p className="text-[#5C6D5E] mb-4">{review.content}</p>
      
      {review.images && review.images.length > 0 && (
        <div className="flex gap-2 mb-4">
          {review.images.map((img, idx) => (
            <img
              key={idx}
              src={img}
              alt={`Review image ${idx + 1}`}
              className="w-20 h-20 object-cover rounded-lg"
            />
          ))}
        </div>
      )}
      
      <button
        onClick={handleHelpful}
        disabled={helpfulClicked}
        className={`flex items-center gap-2 text-sm ${
          helpfulClicked 
            ? "text-[#6B8F71]" 
            : "text-[#5C6D5E] hover:text-[#2D4A3E]"
        } transition-colors`}
      >
        <ThumbsUp className={`w-4 h-4 ${helpfulClicked ? "fill-current" : ""}`} />
        Helpful ({review.helpful_count + (helpfulClicked ? 1 : 0)})
      </button>
    </div>
  );
};

const WriteReviewForm = ({ productSlug, onReviewSubmitted }) => {
  const { token, user } = useAuth();
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!token) {
      toast.error("Please sign in to write a review");
      return;
    }
    
    if (rating === 0) {
      toast.error("Please select a rating");
      return;
    }
    
    if (!title.trim() || !content.trim()) {
      toast.error("Please fill in all fields");
      return;
    }
    
    setSubmitting(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/products/${productSlug}/reviews`,
        { product_id: "", rating, title, content, images: [] },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(`Review submitted! You earned ${response.data.bonus_points} bonus points!`);
      setRating(0);
      setTitle("");
      setContent("");
      onReviewSubmitted();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  };
  
  if (!token) {
    return (
      <div className="bg-[#FDF8F3] rounded-2xl p-6 text-center">
        <p className="text-[#5C6D5E] mb-4">Sign in to write a review and earn loyalty points!</p>
        <div className="flex items-center justify-center gap-2 text-sm text-[#D4A574]">
          <Award className="w-4 h-4" />
          <span>Earn 10-25 bonus points per review</span>
        </div>
      </div>
    );
  }
  
  return (
    <form onSubmit={handleSubmit} className="bg-[#FDF8F3] rounded-2xl p-6">
      <h3 className="font-semibold text-[#2D4A3E] mb-4">Write a Review</h3>
      
      <div className="mb-4">
        <label className="block text-sm text-[#5C6D5E] mb-2">Your Rating</label>
        <StarRating rating={rating} onRate={setRating} interactive size="lg" />
      </div>
      
      <div className="mb-4">
        <label className="block text-sm text-[#5C6D5E] mb-2">Review Title</label>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Summarize your experience"
          className="rounded-xl"
          data-testid="review-title-input"
        />
      </div>
      
      <div className="mb-4">
        <label className="block text-sm text-[#5C6D5E] mb-2">Your Review</label>
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Tell others about your experience with this product..."
          rows={4}
          className="rounded-xl"
          data-testid="review-content-input"
        />
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-[#D4A574]">
          <Award className="w-4 h-4" />
          <span>Earn 10-25 bonus points</span>
        </div>
        <Button
          type="submit"
          disabled={submitting}
          className="bg-[#2D4A3E] hover:bg-[#1F342B] rounded-full"
          data-testid="submit-review-btn"
        >
          {submitting ? "Submitting..." : "Submit Review"}
        </Button>
      </div>
    </form>
  );
};

const ProductReviews = ({ productSlug }) => {
  const [reviews, setReviews] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [showWriteForm, setShowWriteForm] = useState(false);
  
  useEffect(() => {
    fetchReviews();
  }, [productSlug]);
  
  const fetchReviews = async () => {
    try {
      const [reviewsRes, summaryRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/products/${productSlug}/reviews`),
        axios.get(`${BACKEND_URL}/api/products/${productSlug}/reviews/summary`)
      ]);
      setReviews(reviewsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error("Error fetching reviews:", error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleHelpful = async (reviewId) => {
    try {
      await axios.post(`${BACKEND_URL}/api/reviews/${reviewId}/helpful`);
    } catch (error) {
      console.error("Error marking helpful:", error);
    }
  };
  
  const displayedReviews = showAll ? reviews : reviews.slice(0, 3);
  
  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48"></div>
        <div className="h-32 bg-gray-200 rounded"></div>
        <div className="h-24 bg-gray-200 rounded"></div>
      </div>
    );
  }
  
  return (
    <div className="mt-12" data-testid="product-reviews-section">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-[#2D4A3E] font-['Fraunces']">
          Customer Reviews
        </h2>
        <Button
          variant="outline"
          onClick={() => setShowWriteForm(!showWriteForm)}
          className="rounded-full"
          data-testid="write-review-btn"
        >
          {showWriteForm ? "Cancel" : "Write a Review"}
        </Button>
      </div>
      
      {/* Review Summary */}
      {summary && (
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex flex-col md:flex-row gap-8">
            {/* Average Rating */}
            <div className="text-center md:text-left">
              <div className="text-5xl font-bold text-[#2D4A3E] mb-2">
                {summary.average_rating.toFixed(1)}
              </div>
              <StarRating rating={Math.round(summary.average_rating)} />
              <p className="text-sm text-[#5C6D5E] mt-2">
                Based on {summary.total_reviews} review{summary.total_reviews !== 1 ? "s" : ""}
              </p>
            </div>
            
            {/* Rating Breakdown */}
            <div className="flex-1 space-y-2">
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = summary.rating_breakdown[stars] || 0;
                const percentage = summary.total_reviews > 0 
                  ? (count / summary.total_reviews) * 100 
                  : 0;
                return (
                  <div key={stars} className="flex items-center gap-3">
                    <span className="text-sm text-[#5C6D5E] w-16">{stars} stars</span>
                    <Progress value={percentage} className="flex-1 h-2" />
                    <span className="text-sm text-[#5C6D5E] w-8">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
      
      {/* Write Review Form */}
      {showWriteForm && (
        <div className="mb-6">
          <WriteReviewForm 
            productSlug={productSlug} 
            onReviewSubmitted={() => {
              fetchReviews();
              setShowWriteForm(false);
            }} 
          />
        </div>
      )}
      
      {/* Reviews List */}
      {reviews.length === 0 ? (
        <div className="text-center py-12 bg-[#FDF8F3] rounded-2xl">
          <p className="text-[#5C6D5E] mb-4">No reviews yet. Be the first to review this product!</p>
          {!showWriteForm && (
            <Button
              onClick={() => setShowWriteForm(true)}
              className="bg-[#D4A574] hover:bg-[#C49564] text-[#2D4A3E] rounded-full"
            >
              Write the First Review
            </Button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm">
          <div className="divide-y divide-[#E8DFD5] px-6">
            {displayedReviews.map((review) => (
              <ReviewCard 
                key={review.id} 
                review={review} 
                onHelpful={handleHelpful}
              />
            ))}
          </div>
          
          {reviews.length > 3 && (
            <div className="p-4 border-t border-[#E8DFD5]">
              <button
                onClick={() => setShowAll(!showAll)}
                className="w-full flex items-center justify-center gap-2 text-[#2D4A3E] hover:text-[#D4A574] transition-colors"
              >
                {showAll ? (
                  <>
                    Show Less <ChevronUp className="w-4 h-4" />
                  </>
                ) : (
                  <>
                    Show All {reviews.length} Reviews <ChevronDown className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProductReviews;
