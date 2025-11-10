"""
API to verify the stock override is working correctly
"""

import frappe
import inspect


@frappe.whitelist()
def verify_override():
    """Verify that the ERPNext override is actually working"""
    try:
        import erpnext.accounts.doctype.pos_invoice.pos_invoice as pos_module
        
        # Get the source code of the function
        source = inspect.getsource(pos_module.get_pos_reserved_qty_from_table)
        
        # Check which version is being used
        if 'p_item.docstatus == 1' in source:
            status = "❌ FAILED - Still using original buggy code"
            is_fixed = False
        elif 'p_inv.docstatus.isin([0, 1])' in source:
            status = "✅ WORKING - Using fixed code with draft invoice support"
            is_fixed = True
        else:
            status = "⚠️  UNKNOWN - Cannot determine version"
            is_fixed = None
        
        # Get function location
        func_file = pos_module.get_pos_reserved_qty_from_table.__code__.co_filename
        
        return {
            "success": True,
            "status": status,
            "is_fixed": is_fixed,
            "function_file": func_file,
            "source_snippet": source[source.find('docstatus'):source.find('docstatus')+150] if 'docstatus' in source else "Not found"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "❌ ERROR - Could not verify override"
        }
