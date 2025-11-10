#!/usr/bin/env python3
"""
Run diagnostic tests for stock computation
"""
import sys
import os

# Add the ury app path if needed
sys.path.insert(0, '/home/ec2-user/ury')

# Try to import frappe - if it fails, we'll need to run this differently
try:
    import frappe
    
    # Initialize if needed
    if not hasattr(frappe, 'db') or not frappe.db:
        print("Frappe not initialized. This script needs to be run from Frappe bench console.")
        print("\nTo run the tests, use one of these methods:")
        print("\n1. Via bench console:")
        print("   bench --site [site_name] console")
        print("   Then run: exec(open('/home/ec2-user/ury/run_diagnostic_test.py').read())")
        print("\n2. Via API call (if server is running):")
        print("   curl -X POST http://localhost:8000/api/method/ury.ury.api.diagnose_stock_issue.diagnose_stock_issue")
        print("   -H 'Content-Type: application/json'")
        print("   -d '{\"item_code\": \"Sticky Chewy Chocolate\", \"warehouse\": \"Stores - WC\"}'")
        sys.exit(1)
    
    print("=" * 80)
    print("Testing Stock Diagnostic API")
    print("=" * 80)
    
    # Test 1: Verify override
    print("\n1. Testing verify_override...")
    print("-" * 80)
    try:
        result = frappe.call("ury.ury.api.verify_stock_override.verify_override")
        if result.get("success"):
            print(f"✅ Status: {result.get('status')}")
            print(f"   Is Fixed: {result.get('is_fixed')}")
            print(f"   Function File: {result.get('function_file', 'N/A')}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Comprehensive diagnostic
    print("\n2. Testing diagnose_stock_issue...")
    print("-" * 80)
    item_code = "Sticky Chewy Chocolate"
    warehouse = "Stores - WC"
    
    try:
        result = frappe.call(
            "ury.ury.api.diagnose_stock_issue.diagnose_stock_issue",
            item_code=item_code,
            warehouse=warehouse
        )
        
        if result.get("success"):
            print("✅ Diagnostic successful!")
            summary = result.get("summary", {})
            print(f"\nSummary:")
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
                print("\n❌ Override is NOT applied!")
            
            # Check validation
            validation = result.get("diagnostics", {}).get("validation", {})
            if validation.get("calculation_correct"):
                print("✅ Stock calculation is correct")
            else:
                print("❌ Stock calculation mismatch!")
                print(f"   Reserved Qty Diff: {validation.get('reserved_qty_diff', 'N/A')}")
                print(f"   Available Stock Diff: {validation.get('available_stock_diff', 'N/A')}")
        else:
            print(f"❌ Diagnostic failed: {result.get('error')}")
            if result.get("traceback"):
                print("\nTraceback:")
                print(result["traceback"])
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Direct function call
    print("\n3. Testing get_stock_availability directly...")
    print("-" * 80)
    try:
        from ury.ury.overrides.pos_invoice import get_stock_availability
        
        available_stock, is_stock_item = get_stock_availability(item_code, warehouse)
        print(f"✅ Function call successful")
        print(f"   Available Stock: {available_stock}")
        print(f"   Is Stock Item: {is_stock_item}")
        
        # Test with exclude_invoice
        available_stock_excluded, _ = get_stock_availability(item_code, warehouse, exclude_invoice="TEST-INV-001")
        print(f"   Available Stock (with exclude): {available_stock_excluded}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Testing Complete")
    print("=" * 80)
    
except ImportError:
    print("Frappe not available. This script needs to be run from Frappe bench console.")
    print("\nTo run the tests:")
    print("1. bench --site [site_name] console")
    print("2. exec(open('/home/ec2-user/ury/run_diagnostic_test.py').read())")
    sys.exit(1)

