#!/usr/bin/env python3
"""
Test script for the stock diagnostic API.
Run this from the Frappe bench directory or via bench console.
"""

import frappe
import json

def test_diagnostic_api():
    """Test the diagnostic API endpoints"""
    
    print("=" * 80)
    print("Testing Stock Diagnostic API")
    print("=" * 80)
    
    # Test parameters from the error
    item_code = "Sticky Chewy Chocolate"
    warehouse = "Stores - WC"
    
    print(f"\n1. Testing diagnose_stock_issue for:")
    print(f"   Item: {item_code}")
    print(f"   Warehouse: {warehouse}")
    print("-" * 80)
    
    try:
        result = frappe.call(
            "ury.ury.api.diagnose_stock_issue.diagnose_stock_issue",
            item_code=item_code,
            warehouse=warehouse
        )
        
        if result.get("success"):
            print("✅ Diagnostic API call successful!")
            print("\nSummary:")
            summary = result.get("summary", {})
            print(f"  Bin Quantity: {summary.get('bin_qty', 'N/A')}")
            print(f"  Draft Reserved: {summary.get('draft_reserved', 'N/A')}")
            print(f"  Submitted Reserved: {summary.get('submitted_reserved', 'N/A')}")
            print(f"  Total Reserved: {summary.get('total_reserved', 'N/A')}")
            print(f"  Override Reserved: {summary.get('override_reserved', 'N/A')}")
            print(f"  Manual Available: {summary.get('manual_available', 'N/A')}")
            print(f"  Override Available: {summary.get('override_available', 'N/A')}")
            print(f"  Calculation Status: {summary.get('calculation_status', 'N/A')}")
            print(f"  Root Cause: {summary.get('root_cause', 'N/A')}")
            
            # Check override status
            override_status = result.get("diagnostics", {}).get("override_status", {})
            if override_status.get("applied"):
                print("\n✅ Override is properly applied")
            else:
                print("\n❌ Override is NOT applied - this is a problem!")
            
            # Check validation
            validation = result.get("diagnostics", {}).get("validation", {})
            if validation.get("calculation_correct"):
                print("\n✅ Stock calculation is correct")
            else:
                print("\n❌ Stock calculation mismatch detected")
                print(f"   Reserved Qty Diff: {validation.get('reserved_qty_diff', 'N/A')}")
                print(f"   Available Stock Diff: {validation.get('available_stock_diff', 'N/A')}")
            
        else:
            print(f"❌ Diagnostic API call failed: {result.get('error', 'Unknown error')}")
            if result.get("traceback"):
                print("\nTraceback:")
                print(result["traceback"])
        
        # Pretty print full result
        print("\n" + "=" * 80)
        print("Full Diagnostic Result:")
        print("=" * 80)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error calling diagnostic API: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    print("\n" + "=" * 80)
    print("2. Testing verify_override")
    print("-" * 80)
    
    try:
        verify_result = frappe.call("ury.ury.api.verify_stock_override.verify_override")
        if verify_result.get("success"):
            print(f"✅ {verify_result.get('status', 'Unknown status')}")
            print(f"   Function File: {verify_result.get('function_file', 'N/A')}")
        else:
            print(f"❌ Verification failed: {verify_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error calling verify_override: {str(e)}")
    
    print("\n" + "=" * 80)
    print("3. Testing get_stock_availability directly")
    print("-" * 80)
    
    try:
        from ury.ury.overrides.pos_invoice import get_stock_availability
        
        available_stock, is_stock_item = get_stock_availability(item_code, warehouse)
        print(f"✅ Direct function call successful")
        print(f"   Available Stock: {available_stock}")
        print(f"   Is Stock Item: {is_stock_item}")
        
        # Test with exclude_invoice
        available_stock_excluded, _ = get_stock_availability(item_code, warehouse, exclude_invoice="TEST-INV-001")
        print(f"   Available Stock (with exclude): {available_stock_excluded}")
        
    except Exception as e:
        print(f"❌ Error calling get_stock_availability: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    print("\n" + "=" * 80)
    print("Testing Complete")
    print("=" * 80)


if __name__ == "__main__":
    # Initialize Frappe if not already initialized
    if not frappe.db:
        print("Initializing Frappe...")
        frappe.init(site="your-site-name.localhost")  # Update with your site name
        frappe.connect()
    
    test_diagnostic_api()

