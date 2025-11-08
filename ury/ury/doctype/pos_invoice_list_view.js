// Custom List View for POS Invoice to add Payment Type column
frappe.listview_settings['POS Invoice'] = {
    add_fields: ["status", "grand_total"],
    
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
        // Add custom column for Payment Type
        listview.page.add_inner_button(__('Refresh'), function() {
            listview.refresh();
        });
        
        // Override the render method to add payment type column
        const original_render = listview.render_list;
        listview.render_list = function() {
            original_render.call(this);
            this.add_payment_type_column();
        };
        
        listview.add_payment_type_column = function() {
            const me = this;
            // Get payment information for visible invoices
            const invoice_names = this.data.map(d => d.name);
            if (invoice_names.length > 0) {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Sales Invoice Payment',
                        filters: [['parent', 'in', invoice_names]],
                        fields: ['parent', 'mode_of_payment'],
                        limit_page_length: 1000
                    },
                    callback: function(r) {
                        if (r.message) {
                            const payment_map = {};
                            r.message.forEach(payment => {
                                if (!payment_map[payment.parent]) {
                                    payment_map[payment.parent] = payment.mode_of_payment;
                                }
                            });
                            
                            // Add payment type to each row
                            me.$result.find('.list-row').each(function() {
                                const $row = $(this);
                                const invoice_name = $row.find('[data-field="name"]').text().trim();
                                const payment_type = payment_map[invoice_name] || '-';
                                
                                // Add payment type cell if not already added
                                if (!$row.find('.payment-type-cell').length) {
                                    const $payment_cell = $(`<div class="list-row-col ellipsis payment-type-cell" style="flex: 0 0 120px;">
                                        <span class="indicator-pill ${payment_type !== '-' ? 'blue' : 'grey'}">${payment_type}</span>
                                    </div>`);
                                    $row.find('.list-row-col:last').after($payment_cell);
                                }
                            });
                        }
                    }
                });
            }
        };
    }
};
