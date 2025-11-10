"""
Comprehensive diagnostic API to diagnose stock computation issues.
This will test the actual stock availability calculation and identify the root cause.
"""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def diagnose_stock_issue(item_code="Sticky Chewy Chocolate", warehouse="Stores - WC"):
    """
    Comprehensive diagnostic for stock availability issues.
    Tests all aspects of the stock calculation to identify the root cause.
    """
    try:
        results = {
            "item_code": item_code,
            "warehouse": warehouse,
            "diagnostics": {}
        }
        
        # 1. Check if item exists and is a stock item
        item_doc = frappe.get_doc("Item", item_code)
        results["diagnostics"]["item_info"] = {
            "exists": True,
            "is_stock_item": item_doc.is_stock_item,
            "item_name": item_doc.item_name
        }
        
        if not item_doc.is_stock_item:
            return {
                "success": False,
                "error": f"Item {item_code} is not a stock item",
                **results
            }
        
        # 2. Check warehouse exists
        warehouse_exists = frappe.db.exists("Warehouse", warehouse)
        results["diagnostics"]["warehouse_exists"] = warehouse_exists
        
        if not warehouse_exists:
            return {
                "success": False,
                "error": f"Warehouse {warehouse} does not exist",
                **results
            }
        
        # 3. Get actual stock from Bin (MariaDB direct query)
        bin_qty = frappe.db.get_value("Bin", 
            {"item_code": item_code, "warehouse": warehouse}, 
            "actual_qty") or 0
        
        results["diagnostics"]["bin_qty"] = float(bin_qty)
        
        # 4. Get stock ledger entries (for verification)
        sle_qty = frappe.db.sql("""
            SELECT SUM(actual_qty) as total_qty
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s AND warehouse = %s
        """, (item_code, warehouse), as_dict=True)
        
        sle_total = float(sle_qty[0].total_qty) if sle_qty and sle_qty[0].total_qty else 0
        results["diagnostics"]["stock_ledger_total"] = sle_total
        
        # 5. Get draft POS Invoice reservations (docstatus = 0)
        draft_reservations = frappe.db.sql("""
            SELECT 
                pi.name as invoice_name,
                pi.customer,
                pi.creation,
                pii.qty,
                pii.stock_qty,
                pii.warehouse
            FROM `tabPOS Invoice` pi
            INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
            WHERE pii.item_code = %s 
            AND pii.warehouse = %s 
            AND pi.docstatus = 0
            AND IFNULL(pi.consolidated_invoice, '') = ''
            ORDER BY pi.creation DESC
        """, (item_code, warehouse), as_dict=True)
        
        draft_total = sum(float(d.stock_qty) for d in draft_reservations)
        results["diagnostics"]["draft_reservations"] = {
            "count": len(draft_reservations),
            "total_qty": draft_total,
            "details": draft_reservations[:10]  # Limit to first 10
        }
        
        # 6. Get submitted POS Invoice reservations (docstatus = 1)
        submitted_reservations = frappe.db.sql("""
            SELECT 
                pi.name as invoice_name,
                pi.customer,
                pi.creation,
                pii.qty,
                pii.stock_qty,
                pii.warehouse
            FROM `tabPOS Invoice` pi
            INNER JOIN `tabPOS Invoice Item` pii ON pi.name = pii.parent
            WHERE pii.item_code = %s 
            AND pii.warehouse = %s 
            AND pi.docstatus = 1
            AND IFNULL(pi.consolidated_invoice, '') = ''
            ORDER BY pi.creation DESC
        """, (item_code, warehouse), as_dict=True)
        
        submitted_total = sum(float(d.stock_qty) for d in submitted_reservations)
        results["diagnostics"]["submitted_reservations"] = {
            "count": len(submitted_reservations),
            "total_qty": submitted_total,
            "details": submitted_reservations[:10]  # Limit to first 10
        }
        
        # 7. Test our override functions
        from ury.ury.overrides.pos_invoice import (
            get_stock_availability,
            get_pos_reserved_qty,
            get_pos_reserved_qty_from_table
        )
        
        override_reserved_qty = get_pos_reserved_qty(item_code, warehouse)
        override_available_stock, override_is_stock_item = get_stock_availability(item_code, warehouse)
        
        results["diagnostics"]["override_calculations"] = {
            "reserved_qty": float(override_reserved_qty),
            "available_stock": float(override_available_stock),
            "is_stock_item": override_is_stock_item
        }
        
        # 8. Test individual table functions
        pos_item_reserved = get_pos_reserved_qty_from_table("POS Invoice Item", item_code, warehouse)
        packed_item_reserved = get_pos_reserved_qty_from_table("Packed Item", item_code, warehouse)
        
        results["diagnostics"]["override_breakdown"] = {
            "pos_item_reserved": float(pos_item_reserved),
            "packed_item_reserved": float(packed_item_reserved),
            "total_reserved": float(pos_item_reserved + packed_item_reserved)
        }
        
        # 9. Manual calculation for comparison
        manual_total_reserved = draft_total + submitted_total
        manual_available = float(bin_qty) - manual_total_reserved
        
        results["diagnostics"]["manual_calculation"] = {
            "total_reserved": manual_total_reserved,
            "available_stock": manual_available
        }
        
        # 10. Check if override is actually being used
        import erpnext.accounts.doctype.pos_invoice.pos_invoice as pos_module
        import inspect
        
        try:
            source = inspect.getsource(pos_module.get_pos_reserved_qty_from_table)
            override_applied = 'p_inv.docstatus.isin([0, 1])' in source
            results["diagnostics"]["override_status"] = {
                "applied": override_applied,
                "source_snippet": source[source.find('docstatus'):source.find('docstatus')+200] if 'docstatus' in source else "Not found"
            }
        except Exception as e:
            results["diagnostics"]["override_status"] = {
                "applied": "unknown",
                "error": str(e)
            }
        
        # 11. Check for negative stock allowance
        from erpnext.stock.stock_ledger import is_negative_stock_allowed
        negative_allowed = is_negative_stock_allowed(item_code=item_code)
        results["diagnostics"]["negative_stock_allowed"] = negative_allowed
        
        # 12. Calculate expected vs actual
        expected_reserved = manual_total_reserved
        actual_reserved = override_reserved_qty
        reserved_diff = abs(float(expected_reserved) - float(actual_reserved))
        
        expected_available = manual_available
        actual_available = override_available_stock
        available_diff = abs(float(expected_available) - float(actual_available))
        
        results["diagnostics"]["validation"] = {
            "reserved_qty_match": reserved_diff < 0.001,
            "reserved_qty_diff": reserved_diff,
            "available_stock_match": available_diff < 0.001,
            "available_stock_diff": available_diff,
            "calculation_correct": reserved_diff < 0.001 and available_diff < 0.001
        }
        
        # 13. Summary
        results["summary"] = {
            "bin_qty": float(bin_qty),
            "draft_reserved": draft_total,
            "submitted_reserved": submitted_total,
            "total_reserved": manual_total_reserved,
            "override_reserved": float(override_reserved_qty),
            "manual_available": manual_available,
            "override_available": float(override_available_stock),
            "calculation_status": "CORRECT" if reserved_diff < 0.001 and available_diff < 0.001 else "MISMATCH",
            "root_cause": _identify_root_cause(results["diagnostics"])
        }
        
        return {
            "success": True,
            **results
        }
        
    except Exception as e:
        import traceback
        frappe.log_error(f"Stock diagnostic failed: {str(e)}\n{traceback.format_exc()}", "Stock Diagnostic Error")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "item_code": item_code,
            "warehouse": warehouse
        }


def _identify_root_cause(diagnostics):
    """Identify the root cause of the stock issue"""
    issues = []
    
    # Check if override is applied
    if diagnostics.get("override_status", {}).get("applied") != True:
        issues.append("Override not applied - ERPNext buggy code still in use")
    
    # Check if reserved qty matches
    if not diagnostics.get("validation", {}).get("reserved_qty_match"):
        issues.append("Reserved quantity calculation mismatch")
    
    # Check if available stock matches
    if not diagnostics.get("validation", {}).get("available_stock_match"):
        issues.append("Available stock calculation mismatch")
    
    # Check if bin qty is negative
    if diagnostics.get("bin_qty", 0) < 0:
        issues.append("Bin quantity is negative")
    
    # Check if total reserved exceeds bin qty
    total_reserved = diagnostics.get("override_calculations", {}).get("reserved_qty", 0)
    bin_qty = diagnostics.get("bin_qty", 0)
    if total_reserved > bin_qty:
        issues.append(f"Reserved quantity ({total_reserved}) exceeds bin quantity ({bin_qty})")
    
    if not issues:
        return "No obvious issues found - calculation appears correct"
    
    return "; ".join(issues)


@frappe.whitelist()
def test_specific_invoice(invoice_name):
    """
    Test stock availability for a specific invoice that's failing.
    """
    try:
        invoice_doc = frappe.get_doc("POS Invoice", invoice_name)
        
        results = {
            "invoice_name": invoice_name,
            "invoice_status": {
                "docstatus": invoice_doc.docstatus,
                "customer": invoice_doc.customer,
                "warehouse": None,
                "items": []
            }
        }
        
        # Get warehouse from POS Profile
        pos_profile = frappe.get_doc("POS Profile", invoice_doc.pos_profile)
        default_warehouse = pos_profile.warehouse
        results["invoice_status"]["warehouse"] = default_warehouse
        
        # Test each item
        for item in invoice_doc.items:
            item_result = {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "stock_qty": item.stock_qty,
                "warehouse": item.warehouse or default_warehouse
            }
            
            # Get stock availability for this item
            from ury.ury.overrides.pos_invoice import get_stock_availability
            
            available_stock, is_stock_item = get_stock_availability(
                item.item_code, 
                item.warehouse or default_warehouse
            )
            
            item_result["stock_availability"] = {
                "available": float(available_stock),
                "is_stock_item": is_stock_item,
                "required": float(item.stock_qty),
                "sufficient": float(available_stock) >= float(item.stock_qty)
            }
            
            # Run full diagnostic for this item
            diagnostic = diagnose_stock_issue(item.item_code, item.warehouse or default_warehouse)
            item_result["diagnostic"] = diagnostic
            
            results["invoice_status"]["items"].append(item_result)
        
        return {
            "success": True,
            **results
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "invoice_name": invoice_name
        }

