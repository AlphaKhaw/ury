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
    
    // Convert ERPNext format [actual_qty, has_stock] to our expected object format
    const convertedResult: Record<string, StockAvailability> = {};
    
    for (const [itemCode, stockData] of Object.entries(response.message)) {
      if (Array.isArray(stockData) && stockData.length >= 2) {
        const actualQty = stockData[0] || 0;
        convertedResult[itemCode] = {
          item_code: itemCode,
          actual_qty: actualQty,
          projected_qty: actualQty,
          reserved_qty: 0
        };
      } else {
        convertedResult[itemCode] = {
          item_code: itemCode,
          actual_qty: 0,
          projected_qty: 0,
          reserved_qty: 0
        };
      }
    }
    
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