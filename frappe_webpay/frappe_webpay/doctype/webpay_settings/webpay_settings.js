// Copyright (c) 2026, Alianza Chilena Contra la Depresion
// For license information, please see license.txt

frappe.ui.form.on("Webpay Settings", {
	// refresh(frm) {},
	use_integration_test_credentials(frm) {
		frm.call("set_integration_test_credentials").then(() => frm.reload_doc());
	},
});
