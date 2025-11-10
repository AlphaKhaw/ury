#!/bin/bash
# Test script for stock diagnostic API
# Run this from your Frappe bench directory

echo "Testing Stock Diagnostic API..."
echo "================================"
echo ""

# Test 1: Verify override is applied
echo "1. Verifying override is applied..."
bench --site [YOUR_SITE_NAME] console <<EOF
import frappe
result = frappe.call("ury.ury.api.verify_stock_override.verify_override")
print(f"Status: {result.get('status')}")
print(f"Success: {result.get('success')}")
print(f"Is Fixed: {result.get('is_fixed')}")
EOF

echo ""
echo "2. Running comprehensive diagnostic..."
bench --site [YOUR_SITE_NAME] console <<EOF
import frappe
import json

item_code = "Sticky Chewy Chocolate"
warehouse = "Stores - WC"

result = frappe.call(
    "ury.ury.api.diagnose_stock_issue.diagnose_stock_issue",
    item_code=item_code,
    warehouse=warehouse
)

if result.get("success"):
    print("\\n✅ Diagnostic successful!")
    summary = result.get("summary", {})
    print(f"Bin Qty: {summary.get('bin_qty')}")
    print(f"Total Reserved: {summary.get('total_reserved')}")
    print(f"Override Reserved: {summary.get('override_reserved')}")
    print(f"Available: {summary.get('override_available')}")
    print(f"Status: {summary.get('calculation_status')}")
    print(f"Root Cause: {summary.get('root_cause')}")
else:
    print(f"\\n❌ Diagnostic failed: {result.get('error')}")
EOF

echo ""
echo "3. Testing get_stock_availability function directly..."
bench --site [YOUR_SITE_NAME] console <<EOF
from ury.ury.overrides.pos_invoice import get_stock_availability

item_code = "Sticky Chewy Chocolate"
warehouse = "Stores - WC"

available, is_stock = get_stock_availability(item_code, warehouse)
print(f"Available Stock: {available}")
print(f"Is Stock Item: {is_stock}")
EOF

echo ""
echo "Testing complete!"

