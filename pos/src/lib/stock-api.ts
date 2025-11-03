import { call } from './frappe-sdk';

export interface StockAvailability {
  item_code: string;
  actual_qty: number;
  projected_qty: number;
  reserved_qty: number;
}

export interface GetStockAvailabilityResponse {
  message: StockAvailability;
}

export const getStockAvailability = async (itemCode: string, warehouse: string) => {
  try {
    const response = await call.get<GetStockAvailabilityResponse>(
      'erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability',
      {
        item_code: itemCode,
        warehouse: warehouse
      }
    );
    return response.message;
  } catch (error: any) {
    if (error._server_messages) {
      const messages = JSON.parse(error._server_messages);
      const message = JSON.parse(messages[0]);
      throw new Error(message.message);
    }
    throw error;
  }
};

export interface BulkStockAvailabilityResponse {
  message: Record<string, StockAvailability>;
}

export const getBulkStockAvailability = async (items: Array<{item_code: string, warehouse: string}>) => {
  try {
    const response = await call.post<any>(
      'ury.ury_pos.api.get_bulk_stock_availability',
      {
        items: items
      }
    );
    
    // Backend returns objects with {item_code, actual_qty, projected_qty, reserved_qty}
    // or legacy ERPNext format [actual_qty, has_stock] array
    const convertedResult: Record<string, StockAvailability> = {};
    
    // Debug: Log raw response to help diagnose issues
    console.log('Stock API Response:', response.message);
    
    for (const [itemCode, stockData] of Object.entries(response.message)) {
      if (Array.isArray(stockData) && stockData.length >= 2) {
        // Legacy ERPNext format: [actual_qty, has_stock]
        const actualQty = stockData[0] || 0;
        convertedResult[itemCode] = {
          item_code: itemCode,
          actual_qty: actualQty,
          projected_qty: actualQty,
          reserved_qty: 0
        };
      } else if (typeof stockData === 'object' && stockData !== null && !Array.isArray(stockData)) {
        // Modern object format from backend API
        const stockObj = stockData as any; // Backend returns object with item_code, actual_qty, etc.
        
        // Safely parse numeric values - handle strings, numbers, null, undefined
        const parseQty = (val: any): number => {
          if (val === null || val === undefined || val === '') return 0;
          const num = typeof val === 'string' ? parseFloat(val) : Number(val);
          return isNaN(num) ? 0 : num;
        };
        
        const actualQty = parseQty(stockObj.actual_qty);
        const projectedQty = parseQty(stockObj.projected_qty !== undefined ? stockObj.projected_qty : stockObj.actual_qty);
        const reservedQty = parseQty(stockObj.reserved_qty);
        
        convertedResult[itemCode] = {
          item_code: stockObj.item_code || itemCode,
          actual_qty: actualQty,
          projected_qty: projectedQty,
          reserved_qty: reservedQty
        };
        
        // Debug logging to help identify issues
        console.log(`Stock parsed for ${itemCode}:`, {
          raw: stockObj,
          parsed: { actual_qty: actualQty, projected_qty: projectedQty, reserved_qty: reservedQty }
        });
      } else {
        // Fallback for unexpected format
        console.warn(`Unexpected stock data format for ${itemCode}:`, stockData, typeof stockData);
        convertedResult[itemCode] = {
          item_code: itemCode,
          actual_qty: 0,
          projected_qty: 0,
          reserved_qty: 0
        };
      }
    }
    
    console.log('Final converted stock result:', convertedResult);
    return convertedResult;
  } catch (error: any) {
    if (error._server_messages) {
      const messages = JSON.parse(error._server_messages);
      const message = JSON.parse(messages[0]);
      throw new Error(message.message);
    }
    throw error;
  }
};