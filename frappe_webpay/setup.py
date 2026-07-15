"""Deja el sitio listo para probar Webpay Plus en ambiente de Integración.

No se ejecuta solo (no está en ningún hook): se invoca a mano una vez,
vía `bench --site <site> execute frappe_webpay.setup.configure_integration_test_mode`.
Sirve tanto para el primer setup como para reaplicar despues de que el
contenedor se recree (el sitio no persiste, solo esta app).

Credenciales de integración: son las públicas que Transbank publica para
Webpay Plus (ver readme.md, Parte 9.1) — no son secretas, apuntan a
https://webpay3gint.transbank.cl y solo sirven en ese ambiente.
"""

import frappe

INTEGRATION_COMMERCE_CODE = "597055555532"
INTEGRATION_API_KEY = "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"


def configure_integration_test_mode():
	_enable_clp()
	_disable_usd_equivalent()
	_configure_webpay_settings()
	_configure_lms_payment_gateway()
	frappe.db.commit()
	print("Webpay Plus (Integración) configurado. Revisa /app/webpay-settings y /app/lms-settings.")


def _enable_clp():
	if not frappe.db.exists("Currency", "CLP"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "CLP"}).insert(ignore_permissions=True)
	frappe.db.set_value("Currency", "CLP", "enabled", 1)


def _disable_usd_equivalent():
	# Evita que check_multicurrency (lms/lms/utils.py) convierta precios en
	# CLP a USD para compradores fuera de la lista de excepciones — Webpay
	# Plus con este codigo de comercio solo opera en CLP.
	frappe.db.set_single_value("LMS Settings", "show_usd_equivalent", 0)


def _configure_webpay_settings():
	settings = frappe.get_single("Webpay Settings")
	settings.enabled = 1
	settings.environment = "Integration"
	settings.commerce_code = INTEGRATION_COMMERCE_CODE
	settings.api_key_secret = INTEGRATION_API_KEY
	settings.save(ignore_permissions=True)


def _configure_lms_payment_gateway():
	from lms.lms.doctype.lms_settings.lms_settings import check_payments_app

	# check_payments_app() convierte LMS Settings.payment_gateway de Data a
	# Link("Payment Gateway") vía Property Setter — sin esto el campo no
	# acepta "Webpay" como valor válido (ver lms_settings.py).
	check_payments_app()

	frappe.db.set_single_value("LMS Settings", "payment_gateway", "Webpay")
	frappe.db.set_single_value("LMS Settings", "default_currency", "CLP")


def smoke_test_create():
	"""Prueba manual: crea una transaccion real contra el sandbox de
	Integracion de Transbank (no cobra nada) para validar credenciales/SDK
	sin depender de que la return_url sea alcanzable desde afuera. Ver
	`bench --site <site> execute frappe_webpay.setup.smoke_test_create`.
	"""
	frappe.set_user("Administrator")
	settings = frappe.get_single("Webpay Settings")

	checkout_url = settings.get_payment_url(
		amount=50000,
		title="Payment for LMS Course A guide to Frappe Learning",
		description="Prueba de integracion",
		reference_doctype="LMS Course",
		reference_docname="a-guide-to-frappe-learning",
		payer_email="jannat@example.com",
		payer_name="Jannat Patel",
		currency="CLP",
		payment_gateway="Webpay",
		redirect_to="/lms/courses/a-guide-to-frappe-learning",
		payment="test-payment-doc",
	)
	print("CHECKOUT_URL:", checkout_url)
	return checkout_url
