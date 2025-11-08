import frappe

def set_payment_type(doc, method):
    """
    Set the custom_payment_type field based on the first mode of payment
    """
    if doc.doctype == "POS Invoice":
        # Get the first mode of payment from Sales Invoice Payment
        payment_entries = frappe.get_all(
            "Sales Invoice Payment",
            filters={"parent": doc.name},
            fields=["mode_of_payment"],
            order_by="idx asc",
            limit=1
        )
        
        if payment_entries:
            doc.custom_payment_type = payment_entries[0].mode_of_payment
        else:
            doc.custom_payment_type = "Not Set"

def update_payment_type_on_save(doc, method):
    """
    Update mode of payment when POS Invoice is saved
    """
    set_payment_type(doc, method)

def update_payment_type_on_submit(doc, method):
    """
    Update mode of payment when POS Invoice is submitted
    """
    set_payment_type(doc, method)
    # Save the document to persist the mode of payment
    frappe.db.set_value("POS Invoice", doc.name, "custom_payment_type", doc.custom_payment_type)
