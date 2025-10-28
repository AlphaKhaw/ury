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
    const response = await call.post<BulkStockAvailabilityResponse>(
      'ury.ury_pos.api.get_bulk_stock_availability', // This API needs to be created
      {
        items: items
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