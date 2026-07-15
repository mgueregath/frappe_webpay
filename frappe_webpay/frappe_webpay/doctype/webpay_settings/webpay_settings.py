# Copyright (c) 2026, Alianza Chilena Contra la Depresion
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.integrations.utils import create_request_log
from frappe.model.document import Document
from frappe.utils import get_url

from payments.utils import create_payment_gateway

RETURN_PATH = "/api/method/frappe_webpay.api.webpay_return"


class WebpaySettings(Document):
	supported_currencies = ("CLP",)

	def on_update(self):
		# Registra el gateway. LMS Settings.payment_gateway es un Link a
		# "Payment Gateway", asi que sin esto "Webpay" no aparece en ningun selector.
		create_payment_gateway("Webpay", settings="Webpay Settings")

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(
				_("Webpay Plus solo opera en CLP. Moneda recibida: {0}").format(currency),
				title=_("Moneda no soportada"),
			)

	def get_transaction(self):
		from transbank.webpay.webpay_plus.transaction import Transaction

		api_key = self.get_password("api_key_secret", raise_exception=True)

		if self.environment == "Production":
			return Transaction.build_for_production(self.commerce_code, api_key)

		return Transaction.build_for_integration(self.commerce_code, api_key)

	def get_payment_url(self, **kwargs):
		"""Invocado por lms.lms.payments.get_payment_link.

		kwargs confirmados en lms/lms/payments.py:71-83
			amount, title, description, reference_doctype, reference_docname,
			payer_email, payer_name, currency, payment_gateway, redirect_to, payment
		"""
		if not self.enabled:
			frappe.throw(_("La pasarela Webpay esta deshabilitada."))

		# LMS NO llama a validate_transaction_currency por su cuenta:
		# lms.lms.payments.validate_currency existe pero nadie la usa.
		# Hay que validar aqui o no se valida nunca.
		self.validate_transaction_currency(kwargs.get("currency"))

		amount = int(round(float(kwargs.get("amount") or 0)))
		if amount <= 0:
			frappe.throw(_("El monto a pagar debe ser mayor que cero."))

		data = dict(kwargs)
		data["amount"] = amount

		# create_request_log extrae reference_doctype/reference_docname desde `data`,
		# inserta con ignore_permissions y hace commit.
		# El owner queda como el comprador: LMS lo necesita despues (ver api.py).
		integration_request = create_request_log(data, service_name="Webpay")

		# buy_order derivado del nombre del IR: unico, <= 26 caracteres,
		# y permite recuperar el IR en el flujo de timeout, donde NO llega token.
		buy_order = f"lms-{integration_request.name}"[:26]
		session_id = frappe.generate_hash(length=32)

		# LMS lee data["order_id"] para llenar LMS Payment.payment_id
		# (lms/lms/utils.py get_payment_id -> "order_id" para gateways no
		# Razorpay/Stripe). Sin esto el pago queda sin identificador.
		data["order_id"] = buy_order
		integration_request.db_set("data", frappe.as_json(data), update_modified=False)

		try:
			response = self.get_transaction().create(
				buy_order,
				session_id,
				amount,
				get_url(RETURN_PATH),
			)
		except Exception:
			integration_request.db_set("error", frappe.get_traceback(), update_modified=False)
			integration_request.db_set("status", "Failed", update_modified=False)
			frappe.db.commit()
			frappe.log_error(title="Webpay: fallo al crear la transaccion")
			frappe.throw(_("No fue posible iniciar el pago con Webpay. Intenta nuevamente."))

		integration_request.db_set("request_id", response["token"], update_modified=False)
		integration_request.db_set("url", response["url"], update_modified=False)
		integration_request.db_set(
			"output",
			frappe.as_json(
				{
					"token": response["token"],
					"url": response["url"],
					"buy_order": buy_order,
					"session_id": session_id,
				}
			),
			update_modified=False,
		)
		frappe.db.commit()

		return get_url(f"/webpay-checkout?ir={integration_request.name}")
