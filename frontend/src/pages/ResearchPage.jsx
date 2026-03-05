import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  Send, 
  Sparkles, 
  Dog, 
  Loader2,
  Plus,
  MessageSquare,
  Trash2,
  ChevronRight
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import AuthModal from "../components/AuthModal";

const EXAMPLE_QUERIES = [
  "Find calming products for anxious dogs",
  "What are trending cat wellness items?",
  "Show me premium pet supplements with good margins",
  "Research orthopedic dog beds from US warehouses",
  "Find pet anxiety relief products under $50 cost"
];

const ResearchPage = () => {
  const { user, token, API } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showAuth, setShowAuth] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (user && token) {
      fetchSessions();
    }
  }, [user, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(response.data);
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  };

  const loadSession = async (id) => {
    try {
      const response = await axios.get(`${API}/chat/session/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setSessionId(id);
      setMessages(response.data.messages || []);
    } catch (error) {
      toast.error("Failed to load session");
    }
  };

  const startNewSession = () => {
    setSessionId(null);
    setMessages([]);
    setInput("");
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    if (!token) return;
    
    try {
      await axios.delete(`${API}/chat/session/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(sessions.filter(s => s.id !== id));
      if (sessionId === id) {
        startNewSession();
      }
      toast.success("Session deleted");
    } catch (error) {
      toast.error("Failed to delete session");
    }
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post(
        `${API}/chat/send`,
        { query: input, session_id: sessionId },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );

      const assistantMessage = {
        role: "assistant",
        content: response.data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      if (!sessionId) {
        setSessionId(response.data.session_id);
      }
      
      if (user && token) {
        fetchSessions();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || "Failed to get response";
      if (errorMsg.includes("usage limit") || errorMsg.includes("budget") || errorMsg.includes("Balance")) {
        toast.error("AI usage limit reached. Please add balance to your Universal Key.", {
          duration: 8000
        });
      } else {
        toast.error(errorMsg);
      }
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (query) => {
    setInput(query);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const formatMessage = (content) => {
    // Basic formatting for product cards
    const lines = content.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('PRODUCT NAME:')) {
        return <strong key={i} className="text-[#2F3E32] block mt-4 text-lg">{line}</strong>;
      }
      if (line.startsWith('VERDICT:')) {
        const isRecommend = line.includes('RECOMMEND') && !line.includes('INVESTIGATE');
        const isInvestigate = line.includes('INVESTIGATE');
        const isSkip = line.includes('SKIP');
        let badgeClass = 'verdict-recommend';
        if (isInvestigate) badgeClass = 'verdict-investigate';
        if (isSkip) badgeClass = 'verdict-skip';
        return (
          <div key={i} className="mt-2">
            <span className={`verdict-badge ${badgeClass}`}>
              {isRecommend ? 'RECOMMEND' : isInvestigate ? 'INVESTIGATE' : 'SKIP'}
            </span>
            <span className="ml-2 text-sm text-[#57534E]">
              {line.replace('VERDICT:', '').replace('RECOMMEND', '').replace('INVESTIGATE FURTHER', '').replace('SKIP', '').trim()}
            </span>
          </div>
        );
      }
      if (line.includes(':') && !line.startsWith('http')) {
        const [label, ...valueParts] = line.split(':');
        const value = valueParts.join(':').trim();
        if (value && ['SUPPLIER', 'SUPPLIER RATING', 'US WAREHOUSE', 'SUPPLIER COST', 'ESTIMATED US SHIPPING', 'LANDED COST', 'RECOMMENDED RETAIL PRICE', 'GROSS MARGIN', 'EMOTIONAL ANGLE', 'BEST AD HOOK', 'SAFETY', 'RISK FLAGS'].some(k => label.toUpperCase().includes(k))) {
          return (
            <div key={i} className="product-card-metric">
              <span className="product-card-metric-label">{label}:</span>
              <span className="product-card-metric-value">{value}</span>
            </div>
          );
        }
      }
      return <p key={i} className="mb-1">{line}</p>;
    });
  };

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Sessions */}
          <div className="hidden lg:block">
            <div className="card-base p-4 sticky top-24">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-[#2F3E32]">Chat History</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={startNewSession}
                  className="text-[#D4A373] hover:text-[#C89565]"
                  data-testid="new-chat-btn"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              
              {!user ? (
                <div className="text-center py-6">
                  <p className="text-sm text-[#57534E] mb-3">Sign in to save your research</p>
                  <Button
                    onClick={() => setShowAuth(true)}
                    variant="outline"
                    size="sm"
                    className="w-full"
                    data-testid="sidebar-signin-btn"
                  >
                    Sign In
                  </Button>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-2">
                    {sessions.map((session) => (
                      <div
                        key={session.id}
                        onClick={() => loadSession(session.id)}
                        className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors group ${
                          sessionId === session.id 
                            ? 'bg-[#2F3E32]/10 text-[#2F3E32]' 
                            : 'hover:bg-[#F2F0E9]'
                        }`}
                        data-testid={`session-${session.id}`}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <MessageSquare className="w-4 h-4 flex-shrink-0 text-[#D4A373]" />
                          <span className="text-sm truncate">
                            {session.messages?.[0]?.content?.slice(0, 30) || 'New chat'}...
                          </span>
                        </div>
                        <button
                          onClick={(e) => deleteSession(session.id, e)}
                          className="opacity-0 group-hover:opacity-100 text-[#D66D5A] hover:text-[#c95d4a] transition-opacity"
                          data-testid={`delete-session-${session.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            <div className="chat-container" data-testid="chat-container">
              {/* Chat Header */}
              <div className="glass border-b border-stone-100 p-4 flex items-center gap-3 sticky top-0 z-10">
                <div className="w-10 h-10 bg-[#2F3E32] rounded-xl flex items-center justify-center">
                  <Dog className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-[#2F3E32] font-['Fraunces']">PetPulse Sourcing Agent</h2>
                  <p className="text-xs text-[#57534E]">Powered by Claude Opus 4.6</p>
                </div>
              </div>

              {/* Messages */}
              <div className="chat-messages">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12">
                    <div className="w-20 h-20 bg-[#F2F0E9] rounded-2xl flex items-center justify-center mb-6">
                      <Sparkles className="w-10 h-10 text-[#D4A373]" />
                    </div>
                    <h3 className="text-2xl font-semibold text-[#2F3E32] mb-2 font-['Fraunces']">
                      Start Your Product Research
                    </h3>
                    <p className="text-[#57534E] mb-8 max-w-md">
                      Ask me to find winning pet wellness products with verified suppliers, 
                      margin analysis, and trend data.
                    </p>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                      {EXAMPLE_QUERIES.slice(0, 4).map((query, index) => (
                        <button
                          key={index}
                          onClick={() => handleExampleClick(query)}
                          className="text-left p-4 rounded-xl bg-[#F2F0E9] hover:bg-[#E8E6DE] transition-colors text-sm text-[#2F3E32] flex items-center gap-2"
                          data-testid={`example-query-${index}`}
                        >
                          <ChevronRight className="w-4 h-4 text-[#D4A373] flex-shrink-0" />
                          <span>{query}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`animate-fade-in-up ${
                          message.role === 'user' ? 'flex justify-end' : 'flex justify-start'
                        }`}
                        data-testid={`message-${index}`}
                      >
                        <div
                          className={`chat-message ${
                            message.role === 'user' 
                              ? 'chat-message-user' 
                              : 'chat-message-assistant'
                          }`}
                        >
                          {message.role === 'assistant' 
                            ? formatMessage(message.content)
                            : message.content
                          }
                        </div>
                      </div>
                    ))}
                    
                    {isLoading && (
                      <div className="flex justify-start animate-fade-in">
                        <div className="chat-message chat-message-assistant">
                          <div className="typing-indicator">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Input Area */}
              <div className="chat-input-container">
                <form onSubmit={handleSubmit} className="flex gap-3">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about pet wellness products..."
                    className="min-h-[56px] max-h-32 resize-none rounded-xl border-stone-200 focus:ring-2 focus:ring-[#2F3E32]/20 focus:border-[#2F3E32]"
                    disabled={isLoading}
                    data-testid="chat-input"
                  />
                  <Button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="bg-[#2F3E32] hover:bg-[#253229] text-white rounded-xl px-6 h-14"
                    data-testid="send-message-btn"
                  >
                    {isLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </Button>
                </form>
                
                {!user && (
                  <p className="text-xs text-[#57534E] text-center mt-3">
                    <button 
                      onClick={() => setShowAuth(true)} 
                      className="text-[#D4A373] hover:underline"
                      data-testid="inline-signin-btn"
                    >
                      Sign in
                    </button>
                    {" "}to save your research and get 15% off
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
};

export default ResearchPage;
