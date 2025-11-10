"""
Test API to verify the URY POS stock validation override is working correctly.
"""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def test_stock_override(item_code="Sticky Chewy Chocolate", warehouse="Stores - WC"):
    """
    Test the URY stock calculation override and compare with original ERPNext logic.
    """
    try:
        # Import our override functions
        from ury.ury.overrides.pos_invoice import (
            get_stock_availability,
            get_pos_reserved_qty,
            get_pos_reserved_qty_from_table
        )
        
        # Get manual calculations for verification
        bin_qty = frappe.db.get_value("Bin", 
            {"item_code": item_code, "warehouse": warehouse}, 
            "actual_qty") or 0
        
        # Get draft reservations manually
        draft_reservations = frappe.db.sql("""
            SELECT COALESCE(SUM(pii.stock_qty), 0) as reserved
            FROM `tabPOS Invoice` pi
            INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
            WHERE pii.item_code = %s 
            AND pii.warehouse = %s 
            AND pi.docstatus = 0
            AND IFNULL(pi.consolidated_invoice, '') = ''
        """, (item_code, warehouse))[0][0] or 0
        
        # Get submitted reservations manually  
        submitted_reservations = frappe.db.sql("""
            SELECT COALESCE(SUM(pii.stock_qty), 0) as reserved
            FROM `tabPOS Invoice` pi
            INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
            WHERE pii.item_code = %s 
            AND pii.warehouse = %s 
            AND pi.docstatus = 1
            AND IFNULL(pi.consolidated_invoice, '') = ''
        """, (item_code, warehouse))[0][0] or 0
        
        # Test our override functions
        override_reserved_qty = get_pos_reserved_qty(item_code, warehouse)
        override_available_stock, override_is_stock_item = get_stock_availability(item_code, warehouse)
        
        # Test individual table function
        pos_item_reserved = get_pos_reserved_qty_from_table("POS Invoice Item", item_code, warehouse)
        packed_item_reserved = get_pos_reserved_qty_from_table("Packed Item", item_code, warehouse)
        
        expected_total_reserved = float(draft_reservations) + float(submitted_reservations)
        expected_available = float(bin_qty) - expected_total_reserved
        
        return {
            "success": True,
            "item_code": item_code,
            "warehouse": warehouse,
            "manual_calculations": {
                "bin_qty": float(bin_qty),
                "draft_reservations": float(draft_reservations),
                "submitted_reservations": float(submitted_reservations),
                "total_reservations_expected": expected_total_reserved,
                "available_expected": expected_available
            },
            "override_calculations": {
                "pos_item_reserved": float(pos_item_reserved),
                "packed_item_reserved": float(packed_item_reserved),
                "total_reserved": float(override_reserved_qty),
                "available_stock": float(override_available_stock),
                "is_stock_item": override_is_stock_item
            },
            "validation": {
                "reserved_qty_correct": abs(float(override_reserved_qty) - expected_total_reserved) < 0.001,
                "available_stock_correct": abs(float(override_available_stock) - expected_available) < 0.001,
                "fix_status": "WORKING" if abs(float(override_reserved_qty) - expected_total_reserved) < 0.001 else "FAILED"
            },
            "summary": f"Bin: {bin_qty} - Reserved: {override_reserved_qty} = Available: {override_available_stock}"
        }
        
    except Exception as e:
        frappe.log_error(f"Stock override test failed: {str(e)}", "Stock Override Test Error")
        return {
            "success": False,
            "error": str(e),
            "item_code": item_code,
            "warehouse": warehouse
        }


@frappe.whitelist()
def check_draft_invoices_with_sticky_chocolate():
    """
    Check all draft invoices that have Sticky Chewy Chocolate.
    """
    try:
        draft_invoices = frappe.db.sql("""
            SELECT 
                pi.name,
                pi.customer,
                pi.creation,
                pi.grand_total,
                pii.item_code,
                pii.qty,
                pii.stock_qty,
                pii.warehouse
            FROM `tabPOS Invoice` pi
            INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
            WHERE pii.item_code = 'Sticky Chewy Chocolate'
            AND pi.docstatus = 0
            ORDER BY pi.creation DESC
        """, as_dict=True)
        
        return {
            "success": True,
            "draft_invoices": draft_invoices,
            "count": len(draft_invoices)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
