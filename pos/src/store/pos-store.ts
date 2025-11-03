import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { storage } from '../lib/storage';
import { getRestaurantMenu, getAggregatorMenu, MenuItem as APIMenuItem } from '../lib/menu-api';
import { getBulkStockAvailability, StockAvailability, getStockAvailability } from '../lib/stock-api';
import { getCurrencyInfo, PosProfileCombined, getCombinedPosProfile } from '../lib/pos-profile-api';
import { getMenuCourses } from '../lib/menu-course-api';
import { getCustomerGroups, getCustomerTerritories, searchCustomers } from '../lib/customer-api';
import { DEFAULT_ORDER_TYPE, OrderType } from '../data/order-types';
import { getTableOrder, TableOrder } from '../lib/order-api';
import { getPaymentModes } from '../lib/payment-api';

// Constants
const MAX_QUANTITY = 99;
const MIN_QUANTITY = 0;
const ITEMS_PER_PAGE = 10;

// Custom error class for cart operations
class CartError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CartError';
  }
}

// Extend the API MenuItem to include UI-specific properties
export interface MenuItem extends Omit<APIMenuItem, 'rate' | 'item_image'> {
  id: string;
  name: string;
  image: string | null;
  price: number;
  quantity?: number;
  description?: string;
  special_dish?: 1 | 0;
  is_stock_item?: 1 | 0;
  variants?: Array<{ id: string; name: string; price: number }>;
  addons?: Array<{ id: string; name: string; price: number; category: 'sides' | 'drinks' | 'desserts' }>;
  selectedVariant?: { id: string; name: string; price: number };
  selectedAddons?: Array<{ id: string; name: string; price: number }>;
  uniqueId?: string;
  tax_rate?: number;
  instanceId?: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
}

export interface OrderItem extends MenuItem {
  quantity: number;
  selectedVariant?: { id: string; name: string; price: number };
  selectedAddons?: { id: string; name: string; price: number }[];
  uniqueId?: string;
  comment?: string;
  parent_item?: string;
  is_addon?: boolean;
  instanceId?: string; // Added to distinguish separate instances of the same item configuration
}

export interface PaymentMode {
  id: string;
  name: string;
  enabled: boolean;
}

export interface Order {
  id: string;
  cartId: string;
  customerId?: string;
  paymentModeId: string;
  paymentMode: string;
  orderType: OrderType;
  status: 'pending' | 'paid' | 'preparing' | 'ready' | 'completed' | 'cancelled';
  totalAmount: number;
  paidAmount: number;
  createdAt: string;
  updatedAt: string;
}

interface CartTotals {
  subtotal: number;
  tax: number;
  total: number;
  itemCount: number;
}

interface Aggregator {
  customer: string;
}

interface POSState {
  menuItems: MenuItem[];
  categories: string[];
  activeOrders: OrderItem[];
  selectedCategory: string;
  selectedTable: string | null;
  selectedRoom: string | null;
  searchQuery: string;
  selectedCustomer: Customer | null;
  selectedOrderType: OrderType;
  quickFilter: 'all' | 'special';
  selectedItem: MenuItem | null;
  cartId: string | null;
  loading: boolean;
  menuLoading: boolean;
  orderLoading: boolean;
  profileLoading: boolean;
  error: string | null;
  paymentModes: string[];
  orders: Order[];
  selectedAggregator: Aggregator | null;
  currency: string;
  currencySymbol: string | null;
  isUpdatingOrder: boolean;
  orderId: string | null;
  posProfile: PosProfileCombined | null;
  customerGroups: string[];
  territories: string[];
  tableOrder: TableOrder | null;
  isInitializing: boolean;
  orderComment: string;
  defaultCustomers: Record<OrderType, string | null>;
  stockAvailability: Record<string, StockAvailability>;
  stockLoading: Record<string, boolean>;
}

interface POSStore extends POSState {
  fetchMenuItems: () => Promise<void>;
  fetchAggregatorMenu: (aggregator: string) => Promise<void>;
  fetchCategories: () => Promise<void>;
  fetchPaymentModes: () => Promise<void>;
  addToOrder: (item: OrderItem, forceNewInstance?: boolean) => Promise<string | null>;
  removeFromOrder: (uniqueId: string) => Promise<void>;
  updateQuantity: (uniqueId: string, quantity: number) => Promise<void>;
  clearOrder: () => Promise<void>;
  setSelectedCategory: (category: string) => void;
  setSearchQuery: (query: string) => void;
  setSelectedCustomer: (customer: Customer | null) => void;
  setSelectedTable: (table: string | null, room: string | null, doNotLoadOrder?: boolean) => void;
  setSelectedOrderType: (type: OrderType) => void;
  setQuickFilter: (filter: 'all' | 'special') => void;
  setSelectedItem: (item: MenuItem | null) => void;
  initializeCart: () => Promise<void>;
  processPayment: (paymentMode: string, amount: number) => Promise<void>;
  updateOrderStatus: (orderId: string, status: Order['status']) => Promise<void>;
  fetchPosProfile: () => Promise<void>;
  fetchCustomerGroups: () => Promise<void>;
  fetchTerritories: () => Promise<void>;
  fetchCurrencySymbol: () => Promise<void>;
  getCartTotals: () => CartTotals;
  itemExistsInCart: (uniqueId: string) => boolean;
  validateQuantity: (quantity: number) => boolean;
  getItemPrice: (item: OrderItem) => number;
  getItemQuantityFromCart: (item: MenuItem) => number;
  getAddonsForItem: (parentItem: string) => OrderItem[];
  removeItemWithAddons: (uniqueId: string) => Promise<void>;
  loadTableOrder: (table: string) => Promise<void>;
  clearTableOrder: () => void;
  isMenuInteractionDisabled: () => boolean;
  isOrderInteractionDisabled: () => boolean;
  initializeApp: () => Promise<void>;
  setOrderForUpdate: (orderId: string | null) => void;
  resetOrderState: () => void;
  setSelectedAggregator: (aggregator: Aggregator | null) => void;
  setOrderComment: (comment: string) => void;
  setDefaultCustomerForOrderType: (orderType: OrderType, customerId: string | null) => void;
  getDefaultCustomerForOrderType: (orderType: OrderType) => string | null;
  setDefaultCustomerForCurrentOrderType: () => Promise<void>;
  checkStockAvailability: (itemCode: string, warehouse: string) => Promise<StockAvailability>;
  checkBulkStockAvailability: (items: Array<{item_code: string, warehouse: string}>) => Promise<void>;
  updateStockAvailability: (itemCode: string, stockInfo: StockAvailability) => void;
  setStockLoading: (itemCode: string, loading: boolean) => void;
}

const generateUniqueId = (item: OrderItem): string => {
  const variantId = item.selectedVariant?.id || 'default';
  const addonIds = item.selectedAddons?.map(addon => addon.id).sort().join('-') || 'no-addons';
  // Include an instanceId to distinguish separate instances of the same item configuration
  const instanceId = item.instanceId || `default_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  return `${item.id}-${variantId}-${addonIds}-${instanceId}`;
};

const calculateItemPrice = (item: OrderItem): number => {
  const basePrice = item.selectedVariant?.price || item.price;
  const addonsTotal = item.selectedAddons?.reduce((sum, addon) => sum + addon.price, 0) || 0;
  return basePrice + addonsTotal;
};

export const usePOSStore = create<POSStore>((set, get) => ({
  menuItems: [],
  categories: [],
  activeOrders: [],
  selectedCategory: '',
  selectedTable: null,
  selectedRoom: null,
  searchQuery: '',
  selectedCustomer: null,
  selectedOrderType: DEFAULT_ORDER_TYPE as OrderType,
  quickFilter: "all",
  selectedItem: null,
  cartId: null,
  loading: false,
  menuLoading: false,
  orderLoading: false,
  profileLoading: false,
  error: null,
  paymentModes: ['Cash'],
  orders: [],
  posProfile: null,
  customerGroups: [],
  territories: [],
  selectedAggregator: null,
  currency: storage.getItem('currency') || 'INR',
  currencySymbol: storage.getItem('currencySymbol') || null,
  tableOrder: null,
  isInitializing: true,
  isUpdatingOrder: false,
  orderId: null,
  orderComment: '',
  defaultCustomers: (() => {
    // Load from localStorage on initialization
    try {
      const stored = localStorage.getItem('defaultCustomers');
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load default customers from localStorage:', error);
    }
    return {
      'Dine In': null,
      'Take Away': null,
      'Delivery': null,
      'Phone In': null,
      'Aggregators': null,
    };
  })(),
  stockAvailability: {},
  stockLoading: {},

  initializeApp: async () => {
    try {
      set({ isInitializing: true, error: null });
      
      const [profileResult, menuResult, categoriesResult, paymentModesResult] = await Promise.allSettled([
        get().fetchPosProfile(),
        get().fetchMenuItems(),
        get().fetchCategories(),
        get().fetchPaymentModes()
      ]);

      if (profileResult.status === 'rejected' || 
          menuResult.status === 'rejected' || 
          categoriesResult.status === 'rejected' ||
          paymentModesResult.status === 'rejected') {
        set({ 
          error: 'Failed to initialize app. Please refresh the page.',
          isInitializing: false 
        });
        return;
      }

      set({ isInitializing: false });
    } catch (error) {
      set({ 
        error: 'Failed to initialize app. Please refresh the page.',
        isInitializing: false 
      });
    }
  },

  fetchPosProfile: async () => {
    try {
      const cached = sessionStorage.getItem('posProfile');
      if (cached) {
        const profile = JSON.parse(cached);
        set({ 
          posProfile: profile, 
          profileLoading: false,
          currency: profile.currency || 'INR'
        });
        if (!storage.getItem('currencySymbol')) {
          await get().fetchCurrencySymbol();
        }
        return;
      }

      set({ profileLoading: true, error: null });
      const combinedProfile = await getCombinedPosProfile();
      
      sessionStorage.setItem('posProfile', JSON.stringify(combinedProfile));
      set({ 
        posProfile: combinedProfile, 
        profileLoading: false,
        currency: combinedProfile.currency || 'INR'
      });
      
      if (!storage.getItem('currencySymbol')) {
        await get().fetchCurrencySymbol();
      }
    } catch (error) {
      console.error('Error fetching POS profile:', error);
      set({ 
        error: 'Failed to fetch POS profile',
        profileLoading: false 
      });
    }
  },

  fetchCurrencySymbol: async () => {
    try {
      const currency = get().currency;
      const response = await getCurrencyInfo(currency);
      const { symbol } = response;
      
      set({ currencySymbol: symbol });
      storage.setItem('currencySymbol', symbol);
    } catch (error) {
      console.error('Error fetching currency symbol:', error);
      set({ currencySymbol: get().currency });
      storage.setItem('currencySymbol', get().currency);
    }
  },

  fetchMenuItems: async () => {
    const { posProfile, selectedRoom, selectedOrderType } = get();
    if (!posProfile?.restaurant) return;

    try {
      set({ menuLoading: true, error: null });
      const items = await getRestaurantMenu(posProfile.name, selectedRoom, selectedOrderType);
      
      const menuItems: MenuItem[] = items.map(item => ({
        id: item.item,
        name: item.item_name,
        image: item.item_image || null,
        price: typeof item.rate === 'string' ? parseFloat(item.rate) : item.rate || 0,
        item: item.item,
        item_name: item.item_name,
        item_image: item.item_image,
        course: item.course,
        description: item.description || '',
        special_dish: item.special_dish || 0,
        is_stock_item: item.is_stock_item || 0,
        tax_rate: 0,
        addons: item.add_ons?.map(addon => ({
          id: addon.item,
          name: addon.item_name,
          price: addon.rate,
          category: 'sides' as const
        })) || [],
      }));

      set({ menuItems });

      // Now check stock availability for stock-maintaining items only
      if (posProfile?.warehouse) {
        const itemsToCheck = menuItems
          .filter(item => item.is_stock_item === 1) // Only check stock for stock items
          .map(item => ({
            item_code: item.item,
            warehouse: posProfile.warehouse!
          }));
        
        if (itemsToCheck.length > 0) {
          await get().checkBulkStockAvailability(itemsToCheck);
        }
      }
    } catch (error) {
      set({ error: 'Failed to load menu items' });
      console.error('Error loading menu items:', error);
    } finally {
      set({ menuLoading: false });
    }
  },

  fetchAggregatorMenu: async (aggregator: string) => {
    try {
      set({ menuLoading: true, error: null });
      const items = await getAggregatorMenu(aggregator);
      
      const menuItems: MenuItem[] = items.map(item => ({
        ...item,
        id: item.item,
        name: item.item_name,
        image: item.item_image || null,
        price: typeof item.rate === 'string' ? parseFloat(item.rate) : item.rate || 0,
        category: item.course
      }));

      set({ menuItems, menuLoading: false });
    } catch (error) {
      set({ error: 'Failed to load aggregator menu', menuLoading: false });
      console.error('Error loading aggregator menu:', error);
    }
  },

  fetchCategories: async () => {
    try {
      const cached = sessionStorage.getItem('menuCategories');
      if (cached) {
        const categories = JSON.parse(cached);
        set({ categories });
        return;
      }

      const courses = await getMenuCourses();
      const categoryNames = courses.map(course => course.name);
      sessionStorage.setItem('menuCategories', JSON.stringify(categoryNames));
      set({ categories: categoryNames });
    } catch (error) {
      set({ error: 'Failed to load menu categories' });
      throw error;
    }
  },

  fetchPaymentModes: async () => {
    try {
      const modes = await getPaymentModes();
      set({ paymentModes: modes });
    } catch (error) {
      console.error('Failed to fetch payment modes:', error);
    }
  },

  initializeCart: async () => {
    set({ cartId: uuidv4() });
  },

  addToOrder: async (item: OrderItem, forceNewInstance: boolean = false) => {
    try {
      if (!get().validateQuantity(item.quantity)) {
        throw new CartError(`Quantity must be between ${MIN_QUANTITY} and ${MAX_QUANTITY}`);
      }

      // If forcing a new instance, generate a unique instanceId to ensure it's treated as separate
      let uniqueId: string;
      let itemToUse: OrderItem;

      if (forceNewInstance) {
        // Generate a new instanceId to ensure this becomes a separate entry
        const forcedInstanceId = `instance_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        itemToUse = {
          ...item,
          instanceId: forcedInstanceId
        };
        uniqueId = generateUniqueId(itemToUse);
      } else {
        // For non-forced instances, check if item already has an instanceId
        if (!item.instanceId) {
          // Generate a default instanceId if none exists
          const defaultInstanceId = `default_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          itemToUse = {
            ...item,
            instanceId: defaultInstanceId
          };
        } else {
          itemToUse = item;
        }
        uniqueId = generateUniqueId(itemToUse);
      }

      // Only check for existing items if not forcing a new instance
      if (!forceNewInstance) {
        const existingItemIndex = get().activeOrders.findIndex(orderItem => orderItem.uniqueId === uniqueId);

        if (existingItemIndex !== -1) {
          const existingItem = get().activeOrders[existingItemIndex];
          const newQuantity = existingItem.quantity + item.quantity;
          const newComment = item.comment !== undefined ? item.comment : existingItem?.comment || "";

          if (!get().validateQuantity(newQuantity)) {
            throw new CartError(`Cannot add item. Total quantity would exceed ${MAX_QUANTITY}`);
          }

          const newOrders = [...get().activeOrders];
          newOrders[existingItemIndex] = {
            ...existingItem,
            quantity: newQuantity,
            comment: newComment
          };
          
          set({ activeOrders: newOrders });
          return existingItem.uniqueId; // Return the existing uniqueId
        }
      }

      // If we get here, either forcing new instance or no existing item found
      const itemWithUniqueId = { ...itemToUse, uniqueId };
      const newOrders = [...get().activeOrders, itemWithUniqueId];
      set({ activeOrders: newOrders });
      return uniqueId; // Return the new uniqueId
    } catch (error) {
      if (error instanceof CartError) {
        set({ error: error.message });
      } else {
        set({ error: 'Failed to add item to cart' });
      }
      return null; // Return null on error
    }
  },

  removeFromOrder: async (uniqueId: string) => {
    try {
      const newOrders = get().activeOrders.filter(item => item.uniqueId !== uniqueId);
      set({ activeOrders: newOrders });
    } catch (error) {
      set({ error: 'Failed to remove item from cart' });
    }
  },

  updateQuantity: async (uniqueId: string, quantity: number) => {
    try {
      if (!get().validateQuantity(quantity)) {
        throw new CartError(`Quantity must be between ${MIN_QUANTITY} and ${MAX_QUANTITY}`);
      }

      const newOrders = get().activeOrders.map(item =>
        item.uniqueId === uniqueId ? { ...item, quantity } : item
      );
      set({ activeOrders: newOrders });
    } catch (error) {
      if (error instanceof CartError) {
        set({ error: error.message });
      } else {
        set({ error: 'Failed to update quantity' });
      }
    }
  },

  clearOrder: async () => {
    try {
      set({ activeOrders: [] });
    } catch (error) {
      set({ error: 'Failed to clear cart' });
    }
  },

  setSelectedCategory: (category) => set({ selectedCategory: category }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedCustomer: (customer) => set({ selectedCustomer: customer }),
  setSelectedTable: (table: string | null, room: string | null, doNotLoadOrder: boolean = false) => {
    set({ selectedTable: table, selectedRoom: room });
    if (table ) {
      if (!doNotLoadOrder) 
        get().loadTableOrder(table);
    } else {
      get().clearTableOrder();
    }
    if (room) {
      get().fetchMenuItems();
    }
    
    // Set default customer for the current order type when table is selected
    // Only if we're not loading an existing order and not updating an order
    if (table && !get().isUpdatingOrder && !get().orderId) {
      get().setDefaultCustomerForCurrentOrderType();
    }
  },
  setSelectedOrderType: (type) => {
    const { fetchMenuItems, setDefaultCustomerForCurrentOrderType } = get();
    
    set({ 
      activeOrders: [],
      selectedOrderType: type,
      isUpdatingOrder: false,
      orderId: null
    });
    
    // Set the default customer for the new order type if one exists
    // Only set default if we're not updating an existing order
    if (type !== 'Aggregators' && !get().isUpdatingOrder) {
      setDefaultCustomerForCurrentOrderType();
    }
    
    if (type !== 'Aggregators') {
      fetchMenuItems();
    }
  },
  setQuickFilter: (filter) => set({ quickFilter: filter }),
  setSelectedItem: (item) => set({ selectedItem: item }),
  setSelectedAggregator: (aggregator) => set({ selectedAggregator: aggregator }),
  setOrderComment: (comment: string) => set({ orderComment: comment }),
  setDefaultCustomerForOrderType: (orderType: OrderType, customerId: string | null) => {
    set((state) => {
      const newDefaultCustomers = {
        ...state.defaultCustomers,
        [orderType]: customerId
      };
      
      // Persist to localStorage
      localStorage.setItem('defaultCustomers', JSON.stringify(newDefaultCustomers));
      
      return {
        defaultCustomers: newDefaultCustomers
      };
    });
  },
  getDefaultCustomerForOrderType: (orderType: OrderType) => {
    const state = get();
    return state.defaultCustomers[orderType];
  },
  setDefaultCustomerForCurrentOrderType: async () => {
    const { selectedOrderType, getDefaultCustomerForOrderType, setSelectedCustomer } = get();
    const defaultCustomerId = getDefaultCustomerForOrderType(selectedOrderType);
    
    if (defaultCustomerId) {
      try {
        // Try to fetch the actual customer details
        const searchResults = await searchCustomers(defaultCustomerId);
        if (searchResults && searchResults.length > 0) {
          const customer = searchResults[0];
          const name = customer.content?.match(/Customer Name : ([^|]+)/)?.[1]?.trim() || customer.name;
          const phone = customer.content?.match(/Mobile Number : ([^|]+)/)?.[1]?.trim() || '';
          setSelectedCustomer({
            id: customer.name,
            name,
            phone
          });
        } else {
          // If search doesn't work, at least set the ID
          setSelectedCustomer({
            id: defaultCustomerId,
            name: selectedOrderType === 'Dine In' ? 'Walk-in Customer' : 
                  selectedOrderType === 'Take Away' ? 'Take Away Customer' :
                  selectedOrderType === 'Delivery' ? 'Delivery Customer' :
                  selectedOrderType === 'Phone In' ? 'Phone In Customer' :
                  selectedOrderType === 'Aggregators' ? 'Aggregator Customer' : 'Default Customer',
            phone: ''
          });
        }
      } catch (error) {
        console.error('Error fetching default customer:', error);
        // Fallback to setting just the ID with a default name
        setSelectedCustomer({
          id: defaultCustomerId,
          name: selectedOrderType === 'Dine In' ? 'Walk-in Customer' : 
                selectedOrderType === 'Take Away' ? 'Take Away Customer' :
                selectedOrderType === 'Delivery' ? 'Delivery Customer' :
                selectedOrderType === 'Phone In' ? 'Phone In Customer' :
                selectedOrderType === 'Aggregators' ? 'Aggregator Customer' : 'Default Customer',
          phone: ''
        });
      }
    }
  },

  processPayment: async (paymentMode: string, amount: number) => {
    try {
      const { activeOrders, cartId, selectedCustomer, selectedOrderType } = get();
      
      const order: Order = {
        id: uuidv4(),
        cartId: cartId!,
        customerId: selectedCustomer?.id,
        paymentModeId: paymentMode,
        paymentMode,
        orderType: selectedOrderType,
        status: 'paid',
        totalAmount: amount,
        paidAmount: amount,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      const newOrders = [...get().orders, order];
      set({ orders: newOrders });
      
      await get().clearOrder();
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  updateOrderStatus: async (orderId: string, status: Order['status']) => {
    try {
      const newOrders = get().orders.map(order => 
        order.id === orderId 
          ? { ...order, status, updatedAt: new Date().toISOString() }
          : order
      );
      set({ orders: newOrders });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchCustomerGroups: async () => {
    const cached = sessionStorage.getItem('customerGroups');
    if (cached) {
      set({ customerGroups: JSON.parse(cached) });
      return;
    }
    const groups = await getCustomerGroups();
    const names = groups.map((g: any) => g.name);
    set({ customerGroups: names });
    sessionStorage.setItem('customerGroups', JSON.stringify(names));
  },

  fetchTerritories: async () => {
    const cached = sessionStorage.getItem('territories');
    if (cached) {
      set({ territories: JSON.parse(cached) });
      return;
    }
    const terrs = await getCustomerTerritories();
    const names = terrs.map((t: any) => t.name);
    set({ territories: names });
    sessionStorage.setItem('territories', JSON.stringify(names));
  },

  getCartTotals: (): CartTotals => {
    const items = get().activeOrders;
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
    
    const subtotal = items.reduce((sum, item) => {
      const itemPrice = calculateItemPrice(item);
      return sum + (itemPrice * item.quantity);
    }, 0);

    const tax = items.reduce((sum, item) => {
      const itemPrice = calculateItemPrice(item);
      const taxRate = item.tax_rate || 0;
      return sum + (itemPrice * item.quantity * (taxRate / 100));
    }, 0);

    return {
      subtotal,
      tax,
      total: subtotal + tax,
      itemCount
    };
  },

  itemExistsInCart: (uniqueId: string): boolean => {
    return get().activeOrders.some(item => item.uniqueId === uniqueId);
  },

  validateQuantity: (quantity: number): boolean => {
    return !isNaN(quantity) && quantity >= MIN_QUANTITY && quantity <= MAX_QUANTITY;
  },

  getItemPrice: (item: OrderItem): number => {
    return calculateItemPrice(item);
  },

  getItemQuantityFromCart: (item: MenuItem): number => {
    const uniqueId = generateUniqueId(item as OrderItem);
    const cartItem = get().activeOrders.find(orderItem => orderItem.uniqueId === uniqueId);
    return cartItem?.quantity || 0;
  },

  getAddonsForItem: (parentItem: string) => {
    return get().activeOrders.filter(item => 
      item.parent_item === parentItem && item.is_addon
    );
  },

  // Helper function to remove an item and all its add-ons
  removeItemWithAddons: async (uniqueId: string) => {
    try {
      const { activeOrders } = get();
      // Find all add-ons for this item
      const addonsToRemove = activeOrders.filter(item => 
        item.parent_item === uniqueId && item.is_addon
      );
      
      // Remove the main item and all its add-ons
      const newOrders = activeOrders.filter(item => 
        item.uniqueId !== uniqueId && 
        !(item.parent_item === uniqueId && item.is_addon)
      );
      
      set({ activeOrders: newOrders });
    } catch (error) {
      set({ error: 'Failed to remove item and add-ons' });
    }
  },

  loadTableOrder: async (table: string) => {
    try {
      set({ orderLoading: true, error: null });
      const response = await getTableOrder(table);
      const order = response.message;
      if (order && order.name && order.items && order.items.length > 0) {
        const orderItems: OrderItem[] = order.items.map(item => {
          const orderItem = {
            id: item.item_code,
            name: item.item_name,
            price: item.rate,
            quantity: item.qty,
            amount: item.amount,
            image: item.image || null,
            item: item.item_code,
            item_name: item.item_name,
            item_image: null,
            course: '',
            description: item.description || '',
            special_dish: 0 as 0 | 1,
            tax_rate: 0,
          };
          return {
            ...orderItem,
            uniqueId: generateUniqueId(orderItem as OrderItem)
          } as OrderItem;
        });

        set({ 
          tableOrder: response,
          activeOrders: orderItems,
          selectedCustomer: order.customer ? {
            id: order.customer,
            name: order.customer_name,
            phone: order.mobile_number,
          } : null,
          isUpdatingOrder: true,
          orderId: order.name,
        });
      } else {
        set({ 
          tableOrder: null,
          activeOrders: [],
          selectedCustomer: null,
          isUpdatingOrder: false,
          orderId: null,
        });
      }
    } catch (error) {
      set({ 
        error: 'Failed to load table order',
        tableOrder: null,
        activeOrders: [],
        selectedCustomer: null,
        isUpdatingOrder: false,
        orderId: null,
      });
    } finally {
      set({ orderLoading: false });
    }
  },

  clearTableOrder: () => {
    set({ 
      tableOrder: null,
      activeOrders: [],
      selectedCustomer: null,
      isUpdatingOrder: false,
      orderId: null,
    });
  },

  setOrderForUpdate: (orderId: string | null) => {
    set({ 
      isUpdatingOrder: orderId !== null,
      orderId,
    });
  },

  resetOrderState: () => {
    const { fetchMenuItems } = get();
    
    set({
      selectedCustomer: null,
      selectedTable: null,
      selectedRoom: null,
      selectedAggregator: null,
      isUpdatingOrder: false,
      orderId: null,
      activeOrders: [],
      selectedItem: null,
      orderLoading: false,
      menuItems: [],
      error: null,
      selectedOrderType: DEFAULT_ORDER_TYPE,
      orderComment: '',
    });

    fetchMenuItems();
  },

  isMenuInteractionDisabled: () => {
    const state = get();
    return state.menuLoading || state.profileLoading;
  },

  isOrderInteractionDisabled: () => {
    const state = get();
    return state.orderLoading;
  },

  checkStockAvailability: async (itemCode: string, warehouse: string) => {
    try {
      set((state) => ({
        stockLoading: { ...state.stockLoading, [itemCode]: true }
      }));
      
      const stockInfo = await getStockAvailability(itemCode, warehouse);
      
      set((state) => ({
        stockAvailability: { ...state.stockAvailability, [itemCode]: stockInfo },
        stockLoading: { ...state.stockLoading, [itemCode]: false }
      }));
      
      return stockInfo;
    } catch (error) {
      console.error(`Error checking stock availability for item ${itemCode}:`, error);
      set((state) => ({
        stockLoading: { ...state.stockLoading, [itemCode]: false }
      }));
      throw error;
    }
  },

  checkBulkStockAvailability: async (items: Array<{item_code: string, warehouse: string}>) => {
    if (!items.length) return;
    
    try {
      // Set loading state for all items
      set((state) => {
        const newStockLoading = { ...state.stockLoading };
        items.forEach(item => {
          newStockLoading[item.item_code] = true;
        });
        return { stockLoading: newStockLoading };
      });
      
      const stockInfo = await getBulkStockAvailability(items);
      
      // Debug: Log stock info received
      console.log('Stock info received in store:', stockInfo);
      console.log('Items checked:', items.map(i => i.item_code));
      
      set((state) => {
        const newStockAvailability = { ...state.stockAvailability, ...stockInfo };
        console.log('Updated stockAvailability:', newStockAvailability);
        return {
          stockAvailability: newStockAvailability,
          stockLoading: { ...state.stockLoading, ...Object.fromEntries(
            items.map(item => [item.item_code, false])
          ) }
        };
      });
    } catch (error) {
      console.error('Error checking bulk stock availability:', error);
      set((state) => {
        const newStockLoading = { ...state.stockLoading };
        items.forEach(item => {
          newStockLoading[item.item_code] = false;
        });
        return { stockLoading: newStockLoading };
      });
      throw error;
    }
  },

  updateStockAvailability: (itemCode: string, stockInfo: StockAvailability) => {
    set((state) => ({
      stockAvailability: { ...state.stockAvailability, [itemCode]: stockInfo }
    }));
  },

  setStockLoading: (itemCode: string, loading: boolean) => {
    set((state) => ({
      stockLoading: { ...state.stockLoading, [itemCode]: loading }
    }));
  }
})); 