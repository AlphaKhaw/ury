# URY Production Unit & KOT Generation Configuration

## Current Setup: Simplified Cafe Mode (Single Display)

The system is currently configured for **cafe operations** with a single KOT display without production unit filtering.

### Current Behavior:
- ✅ All items generate KOT regardless of item group configuration
- ✅ Single unified display at `/URYMosaic/[production_name]`
- ✅ No overhead for adding new menu items
- ✅ Perfect for cafe/small restaurant operations

---

## Alternative Setup: Restaurant Mode (Multi-Production)

### When to Use Restaurant Mode:
- **Large restaurants** with separate kitchen stations
- **Multi-station operations** (Kitchen + Bar + Bakery)
- **Need for workflow separation** between different preparation areas
- **Want printer routing** to different kitchen printers

### Restaurant Mode Benefits:
1. **🏭 Station Separation**: Kitchen sees food, Bar sees drinks
2. **📺 Multiple Displays**: `/URYMosaic/Kitchen`, `/URYMosaic/Bar`, etc.
3. **🖨️ Printer Routing**: Each station gets its own printers
4. **⚡ Workflow Efficiency**: No cross-contamination of orders

### Restaurant Mode Workflow:
```
Order: Burger + Fries + Coke + Coffee

Production Unit Filtering:
- Burger + Fries → Kitchen Production → Kitchen KOT + Kitchen Printer
- Coke + Coffee → Bar Production → Bar KOT + Bar Printer
```

---

## How to Revert to Restaurant Mode (Production Unit Filtering)

### Step 1: Update KOT Generation Logic

Replace the code in `/ury/ury/api/ury_kot_generate.py` in the `process_items_for_kot` function:

**Current Code (Lines ~128-154):**
```python
    if productions:
        # Check if there's an existing KOT for this invoice
        invoice_exist = frappe.db.exists(
            "URY KOT",
            {
                "invoice": invoice_id,
                "docstatus": 1,
            },
        )
        if invoice_exist:
            kot_type = "Order Modified"

        # Create KOT for all items, using the first production unit
        # This ensures all items get KOT regardless of item group configuration
        primary_production = productions[0]
        
        create_kot_doc(
            invoice_id,
            customer,
            restaurant_table,
            kot_items,  # Use all items instead of filtering
            kot_type,
            comments,
            pos_profile_id,
            kot_naming_series,
            primary_production.name,
        )
```

**Replace With (Restaurant Mode):**
```python
    if productions:
        all_production_item_groups = get_all_production_item_groups(pos_profile.branch)
        
        # Check if any items are not configured in production item groups
        unconfigured_items = []
        for item in kot_items:
            item_group = frappe.db.get_value("Item", item["item_code"], "item_group")
            if item_group not in all_production_item_groups:
                unconfigured_items.append({
                    "item_code": item["item_code"],
                    "item_name": item["item_name"],
                    "item_group": item_group
                })
        
        # If there are unconfigured items, show a helpful message
        if unconfigured_items:
            item_list = ", ".join([f"{item['item_name']} ({item['item_group']})" for item in unconfigured_items])
            frappe.msgprint(
                f"The following items are not assigned to any production unit: {item_list}. "
                f"Please configure their item groups in URY Production Unit settings to generate KOTs.",
                title="Items Not Configured for KOT",
                indicator="yellow"
            )
        
        # Create separate KOTs for each production unit
        for production in productions:
            productionItemGroupslist = frappe.get_all(
                "URY Production Item Groups",
                fields=["item_group"],
                filters={
                    "parent": production.name,
                    "parenttype": "URY Production Unit",
                },
                order_by="idx",
            )
            productionItemGroups = [
                item_group.item_group for item_group in productionItemGroupslist
            ]
            production_items = [
                item
                for item in kot_items
                if frappe.db.get_value("Item", item["item_code"], "item_group")
                in productionItemGroups
            ]

            if production_items:
                invoice_exist = frappe.db.exists(
                    "URY KOT",
                    {
                        "invoice": invoice_id,
                        "docstatus": 1,
                        "production": production.name,
                    },
                )
                if invoice_exist:
                    kot_type = "Order Modified"

                create_kot_doc(
                    invoice_id,
                    customer,
                    restaurant_table,
                    production_items,
                    kot_type,
                    comments,
                    pos_profile_id,
                    kot_naming_series,
                    production.name,
                )
```

### Step 2: Configure Production Units

1. **Create Production Units**:
   - Go to: `URY Production Unit` doctype
   - Create units like: "Kitchen", "Bar", "Bakery"
   - Set POS Profile and Branch for each

2. **Configure Item Groups**:
   - For each production unit, add relevant item groups:
     - **Kitchen**: Food, Main Course, Appetizers, etc.
     - **Bar**: Beverages, Cocktails, Soft Drinks, etc.
     - **Bakery**: Desserts, Pastries, etc.

3. **Setup Printer Routing** (Optional):
   - Configure printers for each production unit
   - KOTs will automatically print to correct printers

### Step 3: Create Multiple Displays

- **Kitchen Display**: `/URYMosaic/Kitchen`
- **Bar Display**: `/URYMosaic/Bar`
- **Bakery Display**: `/URYMosaic/Bakery`

---

## Configuration Guide for Restaurant Mode

### Example Production Unit Setup:

#### Kitchen Production Unit
```
Production: Kitchen
POS Profile: [Your POS Profile]
Item Groups:
- Food
- Main Course
- Appetizers
- Hot Dishes
```

#### Bar Production Unit
```
Production: Bar
POS Profile: [Your POS Profile]  
Item Groups:
- Beverages
- Cocktails
- Soft Drinks
- Coffee
```

### Important Notes:

1. **All Item Groups Must Be Configured**: Any item group not assigned to a production unit will not generate KOT
2. **One Item Group Per Production**: Each item group should only be in one production unit
3. **Display URLs**: Each production unit gets its own display at `/URYMosaic/{production_name}`
4. **Printer Configuration**: Optional but recommended for kitchen printer routing

---

## Current File Locations

- **KOT Generation Logic**: `/ury/ury/api/ury_kot_generate.py`
- **Display Frontend**: `/URYMosaic/src/components/kot.vue`
- **Production Unit Doctype**: `/ury/ury/doctype/ury_production_unit/`
- **Item Groups Doctype**: `/ury/ury/doctype/ury_production_item_groups/`

---

## Decision Matrix

| Feature | Cafe Mode (Current) | Restaurant Mode |
|---------|-------------------|-----------------|
| Setup Complexity | ⭐ Simple | ⭐⭐⭐ Complex |
| Adding Items | ⭐⭐⭐ Easy | ⭐ Requires configuration |
| Display Management | ⭐⭐⭐ Single display | ⭐⭐ Multiple displays |
| Printer Routing | ❌ Manual | ✅ Automatic |
| Kitchen Workflow | ⭐⭐ All items together | ⭐⭐⭐ Separated by station |
| Maintenance Overhead | ⭐⭐⭐ Low | ⭐ High |

**Recommendation**: Keep cafe mode for small operations, switch to restaurant mode for multi-station kitchens.