"""
URY App Installation and Initialization
"""

import frappe


def after_install():
    """Called after URY app is installed"""
    apply_erpnext_overrides()


def after_migrate():
    """Called after database migrations"""
    apply_erpnext_overrides()


def apply_erpnext_overrides():
    """Apply URY overrides to fix ERPNext bugs - called during app initialization"""
    try:
        # Import frappe first
        import frappe
        
        # Force reload the module to ensure we can override it
        import sys
        import importlib
        module_name = 'erpnext.accounts.doctype.pos_invoice.pos_invoice'
        
        # Remove from cache if it exists
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Import the module
        pos_invoice_module = importlib.import_module(module_name)
        
        # Import our fixed functions
        from ury.ury.overrides.pos_invoice import (
            get_pos_reserved_qty_from_table,
            get_pos_reserved_qty,
            get_stock_availability
        )
        
        # Replace the buggy ERPNext functions with our fixed versions
        pos_invoice_module.get_pos_reserved_qty_from_table = get_pos_reserved_qty_from_table
        pos_invoice_module.get_pos_reserved_qty = get_pos_reserved_qty
        pos_invoice_module.get_stock_availability = get_stock_availability
        
        # Override the validate_stock_availablility method at module level (not instance)
        # This avoids pickling issues while ensuring our fixed logic is used
        from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
        
        # Store original method
        original_validate = POSInvoice.validate_stock_availablility
        
        # Create new method that uses our fixed get_stock_availability
        def fixed_validate_stock_availablility(self):
            """Fixed version using our stock availability calculation"""
            if self.is_return:
                return
            
            if self.docstatus.is_draft() and not frappe.db.get_value(
                "POS Profile", self.pos_profile, "validate_stock_on_save"
            ):
                return
            
            from erpnext.stock.stock_ledger import is_negative_stock_allowed
            from frappe.utils import flt
            
            # Use our fixed get_stock_availability
            for d in self.get("items"):
                if not d.serial_and_batch_bundle:
                    if is_negative_stock_allowed(item_code=d.item_code):
                        continue
                    
                    available_stock, is_stock_item = get_stock_availability(
                        d.item_code, 
                        d.warehouse, 
                        exclude_invoice=self.name if self.name else None
                    )
                    
                    item_code_bold = frappe.bold(d.item_code)
                    warehouse_bold = frappe.bold(d.warehouse)
                    
                    if is_stock_item and flt(available_stock) <= 0:
                        frappe.throw(
                            frappe._("Row #{}: Item Code: {} is not available under warehouse {}.").format(
                                d.idx, item_code_bold, warehouse_bold
                            ),
                            title=frappe._("Item Unavailable"),
                        )
                    elif is_stock_item and flt(available_stock) < flt(d.stock_qty):
                        frappe.throw(
                            frappe._("Row #{}: Stock quantity not enough for Item Code: {} under warehouse {}.").format(
                                d.idx, item_code_bold, warehouse_bold
                            ),
                            title=frappe._("Item Unavailable"),
                        )
        
        # Replace at class level using types.MethodType to preserve class identity
        import types
        POSInvoice.validate_stock_availablility = types.MethodType(fixed_validate_stock_availablility, POSInvoice)
        
        frappe.logger().info("URY: Overrode POSInvoice.validate_stock_availablility using MethodType (preserves class identity)")
        
        frappe.logger().info("URY: Applied ERPNext POS Invoice overrides successfully")
        
        # Verify the override worked
        import inspect
        try:
            source = inspect.getsource(pos_invoice_module.get_pos_reserved_qty_from_table)
            if 'p_inv.docstatus.isin([0, 1])' in source:
                frappe.logger().info("URY: Override verification PASSED - using fixed code")
            else:
                frappe.logger().warning("URY: Override verification FAILED - check implementation")
        except:
            frappe.logger().info("URY: Override applied (could not verify source)")
            
    except Exception as e:
        frappe.logger().error(f"URY: Failed to apply ERPNext overrides: {str(e)}")
        import traceback
        frappe.logger().error(f"URY: Traceback: {traceback.format_exc()}")
