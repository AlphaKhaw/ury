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
        # Force reload the module to ensure we can override it
        import sys
        module_name = 'erpnext.accounts.doctype.pos_invoice.pos_invoice'
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        import erpnext.accounts.doctype.pos_invoice.pos_invoice as pos_invoice_module
        from ury.ury.overrides.pos_invoice import (
            get_pos_reserved_qty_from_table,
            get_pos_reserved_qty,
            get_stock_availability
        )
        
        # Replace the buggy ERPNext functions with our fixed versions
        pos_invoice_module.get_pos_reserved_qty_from_table = get_pos_reserved_qty_from_table
        pos_invoice_module.get_pos_reserved_qty = get_pos_reserved_qty
        pos_invoice_module.get_stock_availability = get_stock_availability
        
        frappe.logger().info("URY: Applied ERPNext POS Invoice overrides successfully")
        
        # Verify the override worked
        import inspect
        source = inspect.getsource(pos_invoice_module.get_pos_reserved_qty_from_table)
        if 'p_inv.docstatus.isin([0, 1])' in source:
            frappe.logger().info("URY: Override verification PASSED - using fixed code")
        else:
            frappe.logger().warning("URY: Override verification FAILED - check implementation")
            
    except Exception as e:
        frappe.logger().error(f"URY: Failed to apply ERPNext overrides: {str(e)}")
        import traceback
        frappe.logger().error(f"URY: Traceback: {traceback.format_exc()}")
