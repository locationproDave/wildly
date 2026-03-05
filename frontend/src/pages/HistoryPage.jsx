import React, { useState, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  History, 
  Search, 
  Trash2, 
  Calendar,
  Package,
  ExternalLink
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { format } from "date-fns";

const HistoryPage = () => {
  const { token, API } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data);
    } catch (error) {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const deleteHistoryItem = async (historyId) => {
    try {
      await axios.delete(`${API}/history/${historyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(history.filter(h => h.id !== historyId));
      toast.success("History item deleted");
    } catch (error) {
      toast.error("Failed to delete history item");
    }
  };

  const filteredHistory = history.filter(item =>
    item.query.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupedHistory = filteredHistory.reduce((acc, item) => {
    const date = format(new Date(item.created_at), 'yyyy-MM-dd');
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(item);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="animate-pulse-soft text-[#2F3E32]">Loading history...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-[#2F3E32] mb-2 font-['Fraunces']">
            Search History
          </h1>
          <p className="text-[#57534E]">
            Review your past product research queries
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#A8A29E]" />
          <Input
            placeholder="Search history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 rounded-xl border-stone-200"
            data-testid="search-history-input"
          />
        </div>

        {/* History List */}
        {Object.keys(groupedHistory).length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <History className="w-8 h-8" />
            </div>
            <h3 className="empty-state-title">No search history</h3>
            <p className="empty-state-description">
              Your product research queries will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedHistory)
              .sort(([a], [b]) => new Date(b) - new Date(a))
              .map(([date, items]) => (
                <div key={date}>
                  <div className="flex items-center gap-2 mb-4">
                    <Calendar className="w-4 h-4 text-[#D4A373]" />
                    <h3 className="text-sm font-semibold text-[#2F3E32] uppercase tracking-wide">
                      {format(new Date(date), 'MMMM d, yyyy')}
                    </h3>
                  </div>
                  
                  <div className="space-y-3">
                    {items.map((item, index) => (
                      <div
                        key={item.id}
                        className="card-base p-4 animate-fade-in-up"
                        style={{ animationDelay: `${index * 0.05}s` }}
                        data-testid={`history-item-${item.id}`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-[#2F3E32] mb-1">
                              {item.query}
                            </p>
                            <div className="flex items-center gap-4 text-sm text-[#57534E]">
                              <span className="flex items-center gap-1">
                                <Package className="w-4 h-4" />
                                {item.products_found} products found
                              </span>
                              <span>
                                {format(new Date(item.created_at), 'h:mm a')}
                              </span>
                            </div>
                            {item.response && (
                              <p className="text-sm text-[#57534E] mt-2 line-clamp-2">
                                {item.response}
                              </p>
                            )}
                          </div>
                          
                          <button
                            onClick={() => deleteHistoryItem(item.id)}
                            className="text-[#A8A29E] hover:text-[#D66D5A] transition-colors p-2 flex-shrink-0"
                            data-testid={`delete-history-${item.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
