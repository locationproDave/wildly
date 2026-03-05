import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../App";
import axios from "axios";
import { toast } from "sonner";
import { 
  Send, 
  Loader2,
  Plus,
  Trash2,
  Search,
  Shield,
  FileText,
  BookOpen,
  Megaphone,
  Mail,
  Headphones,
  ChevronRight,
  MessageSquare,
  Sparkles
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import AuthModal from "../components/AuthModal";

const AGENT_ICONS = {
  product_sourcing: Search,
  due_diligence: Shield,
  copywriter: FileText,
  seo_content: BookOpen,
  performance_marketing: Megaphone,
  email_marketing: Mail,
  customer_service: Headphones
};

const AGENT_COLORS = {
  product_sourcing: "#2F3E32",
  due_diligence: "#768A75",
  copywriter: "#D4A373",
  seo_content: "#7CA5B8",
  performance_marketing: "#E8B05C",
  email_marketing: "#D66D5A",
  customer_service: "#57534E"
};

const AGENT_EXAMPLES = {
  product_sourcing: [
    "Find calming products for anxious dogs",
    "What are trending cat wellness items?",
    "Show me pet supplements with good margins"
  ],
  due_diligence: [
    "Verify: Calming Dog Bed from CJdropshipping",
    "Check safety of pet anxiety treats from Zendrop",
    "Validate supplier 'PetComfort Store' on Spocket"
  ],
  copywriter: [
    "Write listing for: Weighted Calming Blanket for Dogs",
    "Create product page for: Calming Cat Cave Bed",
    "Write copy for: Pet Anxiety Supplement Chews"
  ],
  seo_content: [
    "Write blog: 'How to calm an anxious dog during thunderstorms'",
    "Create article: 'Best calming products for cats'",
    "Write post: 'Signs your dog has separation anxiety'"
  ],
  performance_marketing: [
    "Create ad set for: Calming Dog Bed, $49 retail",
    "Write TikTok scripts for: Pet Anxiety Treats",
    "Generate Instagram captions for: Cat Calming Diffuser"
  ],
  email_marketing: [
    "Write abandoned cart flow for: Calming Dog Bed",
    "Create welcome series for new subscribers",
    "Write post-purchase flow for pet supplements"
  ],
  customer_service: [
    "Customer: 'My order hasn't arrived in 2 weeks'",
    "Customer: 'This product didn't work for my dog'",
    "Customer: 'I want to return my order'"
  ]
};

const AgentsPage = () => {
  const { user, token, API } = useAuth();
  const [agents, setAgents] = useState({});
  const [activeAgent, setActiveAgent] = useState("product_sourcing");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [showAuth, setShowAuth] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    if (user && token) {
      fetchSessions();
    }
  }, [user, token, activeAgent]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Reset messages when switching agents
    setMessages([]);
    setSessionId(null);
    setInput("");
  }, [activeAgent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data.agents);
    } catch (error) {
      console.error("Error fetching agents:", error);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/agents/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { agent_type: activeAgent }
      });
      setSessions(response.data);
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  };

  const loadSession = async (id, agentType) => {
    try {
      const response = await axios.get(`${API}/agents/session/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        params: { agent_type: agentType }
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
      await axios.delete(`${API}/agents/session/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { agent_type: activeAgent }
      });
      setSessions(sessions.filter(s => !s.id.includes(id)));
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
        `${API}/agents/chat`,
        { 
          query: input, 
          agent_type: activeAgent,
          session_id: sessionId 
        },
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

  const currentAgent = agents[activeAgent] || {};
  const AgentIcon = AGENT_ICONS[activeAgent] || Search;
  const agentColor = AGENT_COLORS[activeAgent] || "#2F3E32";
  const examples = AGENT_EXAMPLES[activeAgent] || [];

  return (
    <div className="min-h-screen pt-20 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Agent Tabs */}
        <Tabs value={activeAgent} onValueChange={setActiveAgent} className="w-full">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-[#2F3E32] mb-2 font-['Fraunces']">
              AI Agents
            </h1>
            <p className="text-[#57534E] mb-4">
              Specialized AI assistants for every part of your pet wellness business
            </p>
            
            <TabsList className="flex flex-wrap gap-2 bg-transparent h-auto p-0">
              {Object.entries(agents).map(([key, agent]) => {
                const Icon = AGENT_ICONS[key] || Search;
                return (
                  <TabsTrigger
                    key={key}
                    value={key}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all data-[state=active]:text-white data-[state=active]:border-transparent`}
                    style={{
                      backgroundColor: activeAgent === key ? AGENT_COLORS[key] : 'transparent',
                      borderColor: AGENT_COLORS[key]
                    }}
                    data-testid={`agent-tab-${key}`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{agent.name}</span>
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar - Sessions */}
            <div className="hidden lg:block">
              <div className="card-base p-4 sticky top-24">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-[#2F3E32]">{currentAgent.name} History</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={startNewSession}
                    style={{ color: agentColor }}
                    data-testid="new-agent-chat-btn"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                
                {!user ? (
                  <div className="text-center py-6">
                    <p className="text-sm text-[#57534E] mb-3">Sign in to save your work</p>
                    <Button
                      onClick={() => setShowAuth(true)}
                      variant="outline"
                      size="sm"
                      className="w-full"
                      data-testid="agent-sidebar-signin-btn"
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
                          onClick={() => loadSession(session.id.replace(`${activeAgent}_`, ''), activeAgent)}
                          className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors group hover:bg-[#F2F0E9]`}
                          data-testid={`agent-session-${session.id}`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <MessageSquare className="w-4 h-4 flex-shrink-0" style={{ color: agentColor }} />
                            <span className="text-sm truncate">
                              {session.messages?.[0]?.content?.slice(0, 25) || 'New chat'}...
                            </span>
                          </div>
                          <button
                            onClick={(e) => deleteSession(session.id.replace(`${activeAgent}_`, ''), e)}
                            className="opacity-0 group-hover:opacity-100 text-[#D66D5A] hover:text-[#c95d4a] transition-opacity"
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
              <div className="chat-container" data-testid="agent-chat-container">
                {/* Chat Header */}
                <div className="glass border-b border-stone-100 p-4 flex items-center gap-3 sticky top-0 z-10">
                  <div 
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: agentColor }}
                  >
                    <AgentIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-[#2F3E32] font-['Fraunces']">
                      {currentAgent.name || "Agent"}
                    </h2>
                    <p className="text-xs text-[#57534E]">
                      {currentAgent.description || "AI Assistant"}
                    </p>
                  </div>
                </div>

                {/* Messages */}
                <div className="chat-messages">
                  {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12">
                      <div 
                        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
                        style={{ backgroundColor: `${agentColor}20` }}
                      >
                        <AgentIcon className="w-10 h-10" style={{ color: agentColor }} />
                      </div>
                      <h3 className="text-2xl font-semibold text-[#2F3E32] mb-2 font-['Fraunces']">
                        {currentAgent.name || "Agent"}
                      </h3>
                      <p className="text-[#57534E] mb-8 max-w-md">
                        {currentAgent.description || "How can I help you today?"}
                      </p>
                      
                      <div className="grid grid-cols-1 gap-3 w-full max-w-lg">
                        {examples.map((query, index) => (
                          <button
                            key={index}
                            onClick={() => handleExampleClick(query)}
                            className="text-left p-4 rounded-xl bg-[#F2F0E9] hover:bg-[#E8E6DE] transition-colors text-sm text-[#2F3E32] flex items-center gap-2"
                            data-testid={`agent-example-${index}`}
                          >
                            <ChevronRight className="w-4 h-4 flex-shrink-0" style={{ color: agentColor }} />
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
                          data-testid={`agent-message-${index}`}
                        >
                          <div
                            className={`chat-message ${
                              message.role === 'user' 
                                ? 'chat-message-user' 
                                : 'chat-message-assistant'
                            }`}
                            style={message.role === 'user' ? { backgroundColor: agentColor } : {}}
                          >
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          </div>
                        </div>
                      ))}
                      
                      {isLoading && (
                        <div className="flex justify-start animate-fade-in">
                          <div className="chat-message chat-message-assistant">
                            <div className="typing-indicator">
                              <div className="typing-dot" style={{ backgroundColor: agentColor }}></div>
                              <div className="typing-dot" style={{ backgroundColor: agentColor }}></div>
                              <div className="typing-dot" style={{ backgroundColor: agentColor }}></div>
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
                      placeholder={currentAgent.placeholder || "Type your message..."}
                      className="min-h-[56px] max-h-32 resize-none rounded-xl border-stone-200 focus:ring-2 focus:border-transparent"
                      style={{ "--tw-ring-color": `${agentColor}40` }}
                      disabled={isLoading}
                      data-testid="agent-chat-input"
                    />
                    <Button
                      type="submit"
                      disabled={!input.trim() || isLoading}
                      className="text-white rounded-xl px-6 h-14"
                      style={{ backgroundColor: agentColor }}
                      data-testid="agent-send-btn"
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
                        className="hover:underline"
                        style={{ color: agentColor }}
                        data-testid="agent-inline-signin-btn"
                      >
                        Sign in
                      </button>
                      {" "}to save your work and get 15% off
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Tabs>
      </div>

      <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
    </div>
  );
};

export default AgentsPage;
