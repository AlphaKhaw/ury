"""
URY Override for ERPNext POS Invoice functions.

This file contains fixed versions of ERPNext POS Invoice functions that have bugs.
These overrides replace the original ERPNext functions to fix critical issues.
"""

import frappe
from frappe.query_builder.functions import Sum, IfNull
from frappe.utils import flt


def get_pos_reserved_qty_from_table(child_table, item_code, warehouse, exclude_invoice=None):
    """
    FIXED VERSION: Get the total reserved quantity for a given item in POS Invoices
    from a specific child table.

    ORIGINAL BUG: Only counted submitted invoices (docstatus=1)
    FIX: Only count DRAFT invoices (docstatus=0) - submitted invoices have already consumed stock

    Args:
      child_table (str): Name of the child table to query
                (e.g., "POS Invoice Item", "Packed Item").
      item_code (str): The Item Code to filter by.
      warehouse (str): The Warehouse to filter by.
      exclude_invoice (str, optional): Invoice name to exclude from reservation count

    Returns:
      float: The total reserved quantity for the item in the given
                warehouse from DRAFT, unconsolidated POS Invoices only.
    """
    p_inv = frappe.qb.DocType("POS Invoice")
    p_item = frappe.qb.DocType(child_table)

    qty_column = "qty" if child_table == "Packed Item" else "stock_qty"

    # Build the where conditions using & operator (Frappe query builder syntax)
    where_conditions = (
        (p_inv.name == p_item.parent)
        & (IfNull(p_inv.consolidated_invoice, "") == "")
        & (p_inv.docstatus == 0)  # FIXED: Only count DRAFT invoices - submitted invoices already consumed stock
        & (p_item.item_code == item_code)
        & (p_item.warehouse == warehouse)
    )
    
    # Exclude the current invoice if specified (to avoid double-counting during validation)
    if exclude_invoice:
        where_conditions = where_conditions & (p_inv.name != exclude_invoice)

    reserved_qty = (
        frappe.qb.from_(p_inv)
        .from_(p_item)
        .select(Sum(p_item[qty_column]).as_("stock_qty"))
        .where(where_conditions)
    ).run(as_dict=True)

    return flt(reserved_qty[0].stock_qty) if reserved_qty else 0


def get_pos_reserved_qty(item_code, warehouse, exclude_invoice=None):
    """
    FIXED VERSION: Calculate total quantity reserved for the given item and warehouse.

    Includes:
    - Direct sales of the item in DRAFT POS Invoices only (submitted invoices already consumed stock)
    - Sales of the item as a component of a Product Bundle

    Excludes consolidated invoices (already merged into Sales Invoices via
    POS Closing Entry). Used to reflect near real-time availability in the
    POS UI and to prevent overselling while multiple sessions may be active.
    
    Args:
        item_code (str): Item code to check
        warehouse (str): Warehouse to check
        exclude_invoice (str, optional): Invoice name to exclude from reservation count
                                        (useful when validating the invoice itself)
    """
    pinv_item_reserved_qty = get_pos_reserved_qty_from_table("POS Invoice Item", item_code, warehouse, exclude_invoice)
    packed_item_reserved_qty = get_pos_reserved_qty_from_table("Packed Item", item_code, warehouse, exclude_invoice)

    reserved_qty = pinv_item_reserved_qty + packed_item_reserved_qty

    return reserved_qty


@frappe.whitelist()
def get_stock_availability(item_code, warehouse, exclude_invoice=None):
    """
    FIXED VERSION: Get stock availability with proper draft invoice reservation calculation.
    
    Args:
        item_code (str): Item code to check
        warehouse (str): Warehouse to check
        exclude_invoice (str, optional): Invoice name to exclude from reservation count
                                        (useful when validating the invoice itself)
    """
    if frappe.db.get_value("Item", item_code, "is_stock_item"):
        is_stock_item = True
        
        # Import the original bin quantity function (this one works fine)
        from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_bin_qty
        
        bin_qty = get_bin_qty(item_code, warehouse)
        pos_sales_qty = get_pos_reserved_qty(item_code, warehouse, exclude_invoice)  # Use our fixed function

        return bin_qty - pos_sales_qty, is_stock_item
    else:
        is_stock_item = True
        if frappe.db.exists("Product Bundle", {"name": item_code, "disabled": 0}):
            # Import the original bundle availability function (this one works fine)
            from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_bundle_availability
            return get_bundle_availability(item_code, warehouse), is_stock_item
        else:
            is_stock_item = False
            # Is a service item or non_stock item
            return 0, is_stock_item
