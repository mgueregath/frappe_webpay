import json

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.no_cache = 1

	name = frappe.form_dict.get("ir")
	if not name:
		frappe.throw(_("Solicitud de pago no especificada."), frappe.PermissionError)

	request = frappe.db.get_value(
		"Integration Request",
		name,
		["name", "status", "output", "integration_request_service"],
		as_dict=True,
	)

	if (
		not request
		or request.integration_request_service != "Webpay"
		or request.status not in ("Queued", "")
	):
		frappe.throw(_("Solicitud de pago inválida o ya procesada."), frappe.PermissionError)

	output = json.loads(request.output or "{}")

	context.webpay_url = output.get("url")
	context.token = output.get("token")

	if not context.webpay_url or not context.token:
		frappe.throw(_("La transacción no fue inicializada correctamente."))

	return context
