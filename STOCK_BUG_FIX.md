# Stock Computation Bug Fix - Summary

## Issues Identified

### 1. **Critical Bug: Early Return Instead of Continue** (FIXED)
**Location:** `/home/ec2-user/ury/ury/install.py` line 74-75

**Problem:** 
When validating stock availability, if any item allowed negative stock, the validation would return early and skip validation for ALL remaining items. This used `return` instead of `continue`.

**Fix:**
Changed `return` to `continue` so that only the specific item is skipped, and validation continues for other items.

```python
# BEFORE (BUGGY):
if is_negative_stock_allowed(item_code=d.item_code):
    return  # ❌ Skips ALL remaining items

# AFTER (FIXED):
if is_negative_stock_allowed(item_code=d.item_code):
    continue  # ✅ Skips only this item, continues with others
```

### 2. **Double-Counting Issue: Current Invoice Included in Reservations** (FIXED)
**Location:** `/home/ec2-user/ury/ury/ury/overrides/pos_invoice.py`

**Problem:**
When validating a draft invoice, the `get_pos_reserved_qty` function would include the current invoice's items in the reservation count. This caused double-counting:
- Invoice A (draft) has 5 units of Item X
- Bin has 10 units
- Reserved count includes Invoice A: 5 units
- Available: 10 - 5 = 5 units
- When validating Invoice A again, it sees 5 units reserved (from itself), causing validation to fail incorrectly

**Fix:**
Added an optional `exclude_invoice` parameter to:
- `get_pos_reserved_qty_from_table()`
- `get_pos_reserved_qty()`
- `get_stock_availability()`

The validation method now excludes the current invoice from reservation calculations:

```python
available_stock, is_stock_item = get_stock_availability(
    d.item_code, 
    d.warehouse, 
    exclude_invoice=self.name if self.name else None
)
```

## Diagnostic Tools Created

### 1. **Comprehensive Diagnostic API**
**File:** `/home/ec2-user/ury/ury/ury/api/diagnose_stock_issue.py`

**Endpoints:**
- `diagnose_stock_issue(item_code, warehouse)` - Comprehensive diagnostic for stock availability
- `test_specific_invoice(invoice_name)` - Test stock availability for a specific failing invoice

**What it checks:**
1. Item and warehouse existence
2. Actual bin quantity from MariaDB
3. Stock ledger entries
4. Draft POS Invoice reservations
5. Submitted POS Invoice reservations
6. Override function calculations
7. Override application status
8. Negative stock allowance
9. Calculation validation (expected vs actual)
10. Root cause identification

## Testing Instructions

### 1. Test the Diagnostic API
```python
# In Frappe console or via API
frappe.call("ury.ury.api.diagnose_stock_issue.diagnose_stock_issue", 
            item_code="Sticky Chewy Chocolate", 
            warehouse="Stores - WC")
```

### 2. Test a Specific Invoice
```python
frappe.call("ury.ury.api.diagnose_stock_issue.test_specific_invoice", 
            invoice_name="POS-INV-00001")
```

### 3. Verify Override is Applied
```python
frappe.call("ury.ury.api.verify_stock_override.verify_override")
```

## Root Causes Identified

Based on the error message and code analysis, the likely root causes were:

1. **Double-counting**: The current invoice was being counted in its own reservation check
2. **Early return bug**: If any item allowed negative stock, validation would stop for all items
3. **Potential override not applied**: If the override wasn't properly applied, the buggy ERPNext code would still be running

## Next Steps

1. **Rebuild the Docker container** to apply the fixes (as per user's note, code changes need rebuild)
2. **Run the diagnostic API** to verify the fixes are working
3. **Test with the actual failing invoice** to confirm the issue is resolved
4. **Monitor logs** for any remaining issues

## Files Modified

1. `/home/ec2-user/ury/ury/install.py` - Fixed early return bug, added exclude_invoice parameter
2. `/home/ec2-user/ury/ury/ury/overrides/pos_invoice.py` - Added exclude_invoice support to all reservation functions
3. `/home/ec2-user/ury/ury/ury/api/diagnose_stock_issue.py` - New comprehensive diagnostic tool

## Important Notes

- The fixes maintain backward compatibility (exclude_invoice is optional)
- The diagnostic tool can be used to verify the fixes are working correctly
- All changes are in the server code, not the Docker container (as requested)

