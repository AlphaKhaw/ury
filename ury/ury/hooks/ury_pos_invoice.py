import frappe
from datetime import datetime
from frappe.utils import now_datetime, get_time,now


def before_insert(doc, method):
    pos_invoice_naming(doc, method)
    order_type_update(doc, method)
    restrict_existing_order(doc, method)


def validate(doc, method):
    validate_invoice(doc, method)
    validate_customer(doc, method)
    validate_price_list(doc, method)
    # Stock validation: We run our validation in the hook
    # The original validate_stock_availablility will also run, but it will use
    # our overridden get_stock_availability function (from install.py), so both
    # will use the same fixed logic. Our hook runs first to catch issues early.
    validate_stock_availability_in_hook(doc, method)
    # NOTE: We do NOT modify the instance method - that breaks pickling
    # The original method will run after hooks, but it uses our fixed functions


def before_submit(doc, method):
    calculate_and_set_times(doc, method)
    validate_invoice_print(doc, method)
    ro_reload_submit(doc, method)


def on_trash(doc, method):
    table_status_delete(doc, method)


def validate_invoice(doc, method):
    if doc.waiter == None or doc.waiter == "":
        doc.waiter = doc.modified_by
    remove_items = frappe.db.get_value("POS Profile", doc.pos_profile, "remove_items")
    
    if doc.invoice_printed == 1 and remove_items == 0:
        # Get the original items from db
        original_doc = frappe.get_doc("POS Invoice", doc.name)
        
        # Create dictionaries to store both quantities and names
        original_items = {
            item.item_code: {"qty": item.qty, "name": item.item_name} 
            for item in original_doc.items
        }
        current_items = {
            item.item_code: {"qty": item.qty, "name": item.item_name} 
            for item in doc.items
        }
          
        # Check for removed items
        removed_items = set(original_items.keys()) - set(current_items.keys())
        
        # Check for quantity reductions
        reduced_qty_items = []
        for item_code, item_data in original_items.items():
            if (item_code in current_items and 
                current_items[item_code]["qty"] < item_data["qty"]):
                reduced_qty_items.append(
                    f"{item_data['name']} (qty reduced from {item_data['qty']} "
                    f"to {current_items[item_code]['qty']})"
                )
        
        if removed_items or reduced_qty_items:
            error_msg = []
            if removed_items:
                removed_item_names = [
                    original_items[item_code]["name"] 
                    for item_code in removed_items
                ]
                error_msg.append(f"Removed items: {', '.join(removed_item_names)}")
            if reduced_qty_items:
                error_msg.append(f"Modified quantities: {', '.join(reduced_qty_items)}")
                
            frappe.throw(
                ("Cannot modify items after invoice is printed.\n{0}")
                .format("\n".join(error_msg))
            )


def validate_customer(doc, method):
    if doc.customer_name == None or doc.customer_name == "":
        frappe.throw(
            (" Failed to load data , Please Refresh the page ").format(
                doc.customer_name
            )
        )


def calculate_and_set_times(doc, method):
    doc.arrived_time = doc.creation

    current_time_str = now()
    
    current_time = datetime.strptime(current_time_str, "%Y-%m-%d %H:%M:%S.%f")
    
    time_difference = current_time - doc.creation
    
    total_seconds = int(time_difference.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    formatted_spend_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    doc.total_spend_time = formatted_spend_time


def validate_invoice_print(doc, method):
    # Check if the invoice has been printed
    invoice_printed = frappe.db.get_value("POS Invoice", doc.name, "invoice_printed")

    # If the invoice is associated with a restaurant table and hasn't been printed
    if doc.restaurant_table and invoice_printed == 0:
        frappe.throw(
            "Printing the invoice is mandatory before submitting. Please print the invoice."
        )


def table_status_delete(doc, method):
    if doc.restaurant_table:
        frappe.db.set_value(
            "URY Table",
            doc.restaurant_table,
            {"occupied": 0, "latest_invoice_time": None},
        )


def pos_invoice_naming(doc, method):
    pos_profile = frappe.get_doc("POS Profile", doc.pos_profile)
    restaurant = pos_profile.restaurant

    if not doc.restaurant_table:
        doc.naming_series = frappe.db.get_value(
            "URY Restaurant", restaurant, "invoice_series_prefix"
        )
        
        if doc.order_type == "Aggregators":
            doc.naming_series = frappe.db.get_value(
                "URY Restaurant", restaurant, "aggregator_series_prefix"
            )
    


def order_type_update(doc, method):
    if doc.restaurant_table:
        if not doc.order_type:
            is_take_away = frappe.db.get_value(
                "URY Table", doc.restaurant_table, "is_take_away"
            )
            if is_take_away == 1:
                doc.order_type = "Take Away"
            else:
                doc.order_type = "Dine In"
    


# reload restaurant order page if submitted invoice is open there
def ro_reload_submit(doc, method):
    frappe.publish_realtime("reload_ro", {"name": doc.name})


def validate_price_list(doc, method):
        
    if doc.restaurant:
        
        if doc.restaurant_table:
            room = frappe.db.get_value("URY Table", doc.restaurant_table, "restaurant_room")
            menu_name = (
                frappe.db.get_value("URY Restaurant", doc.restaurant, "active_menu")
                if not frappe.db.get_value(
                    "URY Restaurant", doc.restaurant, "room_wise_menu"
                )
                else frappe.db.get_value(
                    "Menu for Room", {"parent": doc.restaurant, "room": room}, "menu"
                )
            )

            doc.selling_price_list = frappe.db.get_value(
                "Price List", dict(restaurant_menu=menu_name, enabled=1)
            )
        
        if doc.order_type == "Aggregators":
            price_list = frappe.db.get_value("Aggregator Settings",
                {"customer": doc.customer, "parent": doc.branch, "parenttype": "Branch"},
                "price_list",
                )
            
            if not price_list:
                frappe.throw(f"Price list for customer {doc.customer} in branch {doc.branch} not found in Aggregator Settings.")
                
            doc.selling_price_list = price_list
            
        else:
            menu_name = frappe.db.get_value("URY Restaurant", doc.restaurant, "active_menu") 

            doc.selling_price_list = frappe.db.get_value(
                "Price List", dict(restaurant_menu=menu_name, enabled=1)
            )
            

def restrict_existing_order(doc, event):
    if doc.restaurant_table:
        invoice_exist = frappe.db.exists(
            "POS Invoice",
            {
                "restaurant_table": doc.restaurant_table,
                "docstatus": 0,
                "invoice_printed": 0,
            },
        )
        if invoice_exist:
            frappe.throw(
                ("Table {0} has an existing invoice").format(doc.restaurant_table)
            )


def validate_stock_availability_in_hook(doc, method):
    """
    Validate stock availability using our fixed stock calculation.
    This runs in the hook BEFORE the original validate_stock_availablility is called.
    We then prevent the original from running to avoid double validation.
    """
    if doc.is_return:
        return
    
    if doc.docstatus.is_draft() and not frappe.db.get_value(
        "POS Profile", doc.pos_profile, "validate_stock_on_save"
    ):
        return
    
    from erpnext.stock.stock_ledger import is_negative_stock_allowed
    from frappe.utils import flt
    from ury.ury.overrides.pos_invoice import get_stock_availability
    
    for d in doc.get("items"):
        if not d.serial_and_batch_bundle:
            # Skip validation for this item if negative stock is allowed
            if is_negative_stock_allowed(item_code=d.item_code):
                continue
            
            # Use our fixed get_stock_availability
            # Exclude current invoice from reservation count to avoid double-counting
            available_stock, is_stock_item = get_stock_availability(
                d.item_code, 
                d.warehouse, 
                exclude_invoice=doc.name if doc.name else None
            )
            
            item_code_bold = frappe.bold(d.item_code)
            warehouse_bold = frappe.bold(d.warehouse)
            
            if is_stock_item and flt(available_stock) <= 0:
                frappe.throw(
                    frappe._("Row #{}: Item Code: {} is not available under warehouse {}.").format(
                        d.idx, item_code_bold, warehouse_bold
                    ),
                    title=frappe._("Item Unavailable"),
                )
            elif is_stock_item and flt(available_stock) < flt(d.stock_qty):
                frappe.throw(
                    frappe._("Row #{}: Stock quantity not enough for Item Code: {} under warehouse {}.").format(
                        d.idx, item_code_bold, warehouse_bold
                    ),
                    title=frappe._("Item Unavailable"),
                )
