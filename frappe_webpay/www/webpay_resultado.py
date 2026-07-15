import json

import frappe

no_cache = 1


def get_branding():
	"""Reads the `webpay_result_branding` hook (see hooks.py) so a theme app
	can restyle this page with its own CSS classes without frappe_webpay
	depending on it. Frappe merges dict-valued hooks across apps into
	{key: [value_from_each_app, ...]}; last app installed wins per key.
	Missing keys fall back to frappe_webpay's own generic classes/CSS,
	defined inline in webpay-resultado.html.
	"""
	branding = frappe.get_hooks("webpay_result_branding") or {}
	return frappe._dict({key: values[-1] for key, values in branding.items() if values})


def get_context(context):
	context.no_cache = 1
	context.branding = get_branding()

	name = frappe.form_dict.get("ir")
	context.estado = "desconocido"

	if not name:
		return context

	request = frappe.db.get_value(
		"Integration Request",
		name,
		["name", "status", "data", "output", "error", "integration_request_service"],
		as_dict=True,
	)

	if not request or request.integration_request_service != "Webpay":
		return context

	data = frappe._dict(json.loads(request.data or "{}"))
	output = frappe._dict(json.loads(request.output or "{}"))
	commit = frappe._dict(output.get("commit") or {})

	context.estado = request.status
	context.aprobado = request.status == "Completed"
	context.error = request.error
	context.titulo = data.get("title")
	context.orden = output.get("buy_order")
	context.monto = commit.get("amount") or data.get("amount")
	context.moneda = data.get("currency")
	context.autorizacion = commit.get("authorization_code")
	context.fecha = commit.get("transaction_date")
	context.tipo_pago = commit.get("payment_type_code")
	context.cuotas = commit.get("installments_number")
	context.tarjeta = (commit.get("card_detail") or {}).get("card_number")
	context.continuar = data.get("redirect_to") or "/lms"

	return context
