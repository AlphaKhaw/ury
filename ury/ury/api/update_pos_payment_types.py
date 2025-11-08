import frappe

@frappe.whitelist()
def update_existing_pos_payment_types():
    """
    Update existing POS Invoices with their mode of payment
    """
    try:
        # Get all POS Invoices that don't have mode of payment set
        pos_invoices = frappe.get_all(
            "POS Invoice",
            filters={
                "docstatus": ["!=", 2],  # Not cancelled
                "custom_payment_type": ["in", [None, "", "Not Set"]]
            },
            fields=["name"],
            limit=1000
        )
        
        updated_count = 0
        
        for invoice in pos_invoices:
            # Get the first mode of payment for this invoice
            payment_entries = frappe.get_all(
                "Sales Invoice Payment",
                filters={"parent": invoice.name},
                fields=["mode_of_payment"],
                order_by="idx asc",
                limit=1
            )
            
            payment_type = "Not Set"
            if payment_entries:
                payment_type = payment_entries[0].mode_of_payment
            
            # Update the POS Invoice
            frappe.db.set_value("POS Invoice", invoice.name, "custom_payment_type", payment_type)
            updated_count += 1
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Updated {updated_count} POS Invoices with mode of payment",
            "updated_count": updated_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating POS mode of payment: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
