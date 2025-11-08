import { useEffect, useMemo } from 'react';
import { usePOSStore } from '../store/pos-store';
import MenuCard from './MenuCard';
import { Spinner } from './ui/spinner';
import { cn } from '../lib/utils';

interface MenuListProps {
  onItemClick: (item: any) => void;
}

const MenuList: React.FC<MenuListProps> = ({ onItemClick }) => {
  const {
    menuItems,
    menuLoading,
    error,
    selectedCategory,
    searchQuery,
    quickFilter,
    fetchMenuItems,
    isMenuInteractionDisabled,
    isOrderInteractionDisabled,
    stockAvailability,
    stockLoading
  } = usePOSStore();

  useEffect(() => {
    fetchMenuItems();
  }, [fetchMenuItems]);

  const filteredItems = useMemo(() => {
    return menuItems.filter(item => {
      const searchTerm = searchQuery.toLowerCase();
      const matchesCategory = !selectedCategory || item.course === selectedCategory;
      const matchesSearch = !searchQuery || 
        item.name.toLowerCase().includes(searchTerm) ||
        item.item.toLowerCase().includes(searchTerm);
      const matchesFilter = quickFilter === 'all' || 
        (quickFilter === 'special' && item.special_dish === 1);
      
      return matchesCategory && matchesSearch && matchesFilter;
    });
  }, [menuItems, selectedCategory, searchQuery, quickFilter]);

  const isInteractionDisabled = isMenuInteractionDisabled() || isOrderInteractionDisabled();

  return (
    <div className="flex-1 overflow-auto bg-gray-50">
      <div className="max-w-screen-xl mx-auto p-4 pb-40">
        {menuLoading ? (
          <div className="h-96">
            <Spinner message="Loading menu items..." />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-red-600 text-center">
              <p className="text-lg font-medium">Error loading menu items</p>
              <p className="text-sm mt-2">{error}</p>
            </div>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-gray-500 text-center">
              <p className="text-lg font-medium">No items found</p>
              <p className="text-sm mt-2">Try adjusting your filters or search term</p>
            </div>
          </div>
        ) : (
          <div className={cn(
            "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3",
            isInteractionDisabled && "opacity-50 pointer-events-none"
          )}>
            {filteredItems.map((item) => {
              // Debug stock lookup for stock items
              if (item.is_stock_item === 1) {
                // Try both item.id and item.item as keys (item.item is the actual item_code)
                const stockDataById = stockAvailability[item.id];
                const stockDataByItemCode = stockAvailability[item.item];
                const stockData = stockDataById || stockDataByItemCode;
                
                if (!stockData) {
                  console.warn(`No stock data found for item ${item.id} (item_code: ${item.item}). Available keys:`, Object.keys(stockAvailability));
                } else {
                  console.log(`Stock for ${item.id} (${item.item}):`, stockData);
                }
              }
              
              // Use item.item (item_code) as the key for stock data lookup since that's what the API uses
              const stockKey = item.item; // Use item_code instead of item.id
              
              return (
                <MenuCard
                  key={item.id}
                  id={item.id}
                  name={item.name}
                  price={item.price}
                  item_image={item.image}
                  course={item.course}
                  item={item.item}
                  onClick={() => onItemClick(item)}
                  disabled={isInteractionDisabled}
                  stockQty={item.is_stock_item === 1 ? stockAvailability[stockKey]?.actual_qty : undefined}
                  hasStock={item.is_stock_item === 1 ? (stockAvailability[stockKey]?.actual_qty > 0) : undefined}
                  stockLoading={item.is_stock_item === 1 ? stockLoading[stockKey] : false}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MenuList; 