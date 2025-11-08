// Custom List View for POS Invoice to add Mode of Payment column
frappe.listview_settings['POS Invoice'] = {
    add_fields: ["status", "grand_total", "custom_payment_type"],
    
    get_indicator: function(doc) {
        if (doc.status === "Paid") {
            return [__("Paid"), "green", "status,=,Paid"];
        } else if (doc.status === "Draft") {
            return [__("Draft"), "red", "status,=,Draft"];
        } else if (doc.status === "Return") {
            return [__("Return"), "darkgrey", "status,=,Return"];
        } else if (doc.status === "Consolidated") {
            return [__("Consolidated"), "blue", "status,=,Consolidated"];
        }
    },
    
    onload: function(listview) {
        // Add custom column for Mode of Payment
        listview.page.add_inner_button(__('Refresh'), function() {
            listview.refresh();
        });
    }
};
