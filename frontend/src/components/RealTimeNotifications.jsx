import React, { useEffect, useState } from 'react';
import { useWebSocket, NotificationType } from '../hooks/useWebSocket';
import { 
  Bell, 
  ShoppingBag, 
  Package, 
  AlertTriangle, 
  UserPlus,
  DollarSign,
  X,
  Wifi,
  WifiOff
} from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './ui/dropdown-menu';
import { toast } from 'sonner';

const getNotificationIcon = (type) => {
  switch (type) {
    case NotificationType.NEW_ORDER:
      return <ShoppingBag className="w-4 h-4 text-green-600" />;
    case NotificationType.ORDER_UPDATE:
      return <Package className="w-4 h-4 text-blue-600" />;
    case NotificationType.LOW_STOCK:
      return <AlertTriangle className="w-4 h-4 text-red-600" />;
    case NotificationType.NEW_CUSTOMER:
      return <UserPlus className="w-4 h-4 text-purple-600" />;
    case NotificationType.REVENUE_UPDATE:
      return <DollarSign className="w-4 h-4 text-green-600" />;
    default:
      return <Bell className="w-4 h-4 text-gray-600" />;
  }
};

const getNotificationTitle = (notification) => {
  switch (notification.type) {
    case NotificationType.NEW_ORDER:
      return `New Order: ${notification.data?.order_number || 'Unknown'}`;
    case NotificationType.ORDER_UPDATE:
      return `Order ${notification.data?.order_number} → ${notification.data?.status}`;
    case NotificationType.LOW_STOCK:
      return `Low Stock: ${notification.data?.product_name}`;
    case NotificationType.NEW_CUSTOMER:
      return `New Customer: ${notification.data?.email}`;
    case NotificationType.REVENUE_UPDATE:
      return `+$${notification.data?.amount?.toFixed(2)} Revenue`;
    default:
      return 'New Notification';
  }
};

const getNotificationDescription = (notification) => {
  switch (notification.type) {
    case NotificationType.NEW_ORDER:
      return `$${notification.data?.total?.toFixed(2)} • ${notification.data?.items_count} items`;
    case NotificationType.ORDER_UPDATE:
      return `Status changed to ${notification.data?.status}`;
    case NotificationType.LOW_STOCK:
      return `Only ${notification.data?.stock_quantity} units left`;
    case NotificationType.NEW_CUSTOMER:
      return notification.data?.name || 'Just signed up';
    case NotificationType.REVENUE_UPDATE:
      return `From order ${notification.data?.order_number}`;
    default:
      return '';
  }
};

const RealTimeNotifications = () => {
  const { isConnected, notifications, lastMessage, clearNotifications } = useWebSocket('admin');
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  // Show toast for new notifications
  useEffect(() => {
    if (lastMessage && !isOpen) {
      const title = getNotificationTitle(lastMessage);
      const description = getNotificationDescription(lastMessage);
      
      if (lastMessage.type === NotificationType.NEW_ORDER) {
        toast.success(title, { description });
      } else if (lastMessage.type === NotificationType.LOW_STOCK) {
        toast.warning(title, { description });
      } else {
        toast.info(title, { description });
      }
      
      setUnreadCount(prev => prev + 1);
    }
  }, [lastMessage, isOpen]);

  // Reset unread count when dropdown opens
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
    }
  }, [isOpen]);

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative rounded-full"
          data-testid="notifications-btn"
        >
          <Bell className="w-5 h-5 text-[#2D4A3E]" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
          <span className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 max-h-96 overflow-y-auto">
        <div className="flex items-center justify-between px-3 py-2 border-b">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[#2D4A3E]">Notifications</span>
            {isConnected ? (
              <Badge className="bg-green-100 text-green-800 text-xs">
                <Wifi className="w-3 h-3 mr-1" />
                Live
              </Badge>
            ) : (
              <Badge className="bg-gray-100 text-gray-600 text-xs">
                <WifiOff className="w-3 h-3 mr-1" />
                Offline
              </Badge>
            )}
          </div>
          {notifications.length > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-xs text-[#5C6D5E]"
              onClick={clearNotifications}
            >
              Clear all
            </Button>
          )}
        </div>
        
        {notifications.length === 0 ? (
          <div className="px-3 py-8 text-center text-[#5C6D5E]">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No notifications yet</p>
            <p className="text-xs">Real-time updates will appear here</p>
          </div>
        ) : (
          <div className="py-1">
            {notifications.map((notification, index) => (
              <DropdownMenuItem 
                key={index} 
                className="flex items-start gap-3 px-3 py-3 cursor-default"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#2D4A3E] truncate">
                    {getNotificationTitle(notification)}
                  </p>
                  <p className="text-xs text-[#5C6D5E]">
                    {getNotificationDescription(notification)}
                  </p>
                </div>
              </DropdownMenuItem>
            ))}
          </div>
        )}
        
        <DropdownMenuSeparator />
        <div className="px-3 py-2 text-center">
          <span className="text-xs text-[#5C6D5E]">
            {isConnected ? 'Connected to real-time updates' : 'Reconnecting...'}
          </span>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default RealTimeNotifications;
