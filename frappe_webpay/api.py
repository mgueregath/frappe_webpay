import json

import frappe
from frappe import _
from frappe.utils import get_url


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def webpay_return():
	"""Retorno de Webpay Plus.

	allow_guest es obligatorio: el retorno por POST (anulación en integración)
	es cross-site, y las cookies de Frappe son SameSite=Lax, así que el navegador
	NO envía la sesión. Este endpoint nunca debe depender de frappe.session.user.
	"""
	# Leer form_dict ANTES de cualquier frappe.set_user():
	# set_user() hace local.form_dict = _dict() y borra todo (frappe/__init__.py).
	token = frappe.form_dict.get("token_ws")
	aborted_token = frappe.form_dict.get("TBK_TOKEN")
	buy_order = frappe.form_dict.get("TBK_ORDEN_COMPRA")

	request_name = resolve_request(token, aborted_token, buy_order)

	if not request_name:
		return redirect_to_url(get_url("/webpay-resultado?estado=desconocido"))

	# Flujo 4: si llega TBK_TOKEN, hubo un error. No se confirma, aunque venga token_ws.
	if aborted_token:
		close(request_name, "Cancelled", "Pago anulado o error en el formulario de Webpay")
		return redirect_to_result(request_name)

	# Flujo 2: timeout. No hay token que confirmar.
	if not token:
		close(request_name, "Cancelled", "Tiempo de espera agotado en el formulario de Webpay")
		return redirect_to_result(request_name)

	# Flujo 1: confirmar.
	commit_transaction(request_name, token)
	return redirect_to_result(request_name)


def resolve_request(token, aborted_token, buy_order):
	"""Localiza el Integration Request sin confiar en la sesión del navegador."""
	for candidate in (token, aborted_token):
		if candidate:
			name = frappe.db.get_value(
				"Integration Request",
				{"request_id": candidate, "integration_request_service": "Webpay"},
				"name",
			)
			if name:
				return name

	# Timeout: solo tenemos la orden de compra, que construimos como f"lms-{ir.name}".
	if buy_order and buy_order.startswith("lms-"):
		name = buy_order[4:]
		if frappe.db.exists(
			"Integration Request", {"name": name, "integration_request_service": "Webpay"}
		):
			return name

	return None


def close(request_name, status, message):
	request = frappe.get_doc("Integration Request", request_name, for_update=True)

	if request.status == "Completed":
		return

	request.db_set("status", status, update_modified=False)
	request.db_set("error", message, update_modified=False)
	frappe.db.commit()


def commit_transaction(request_name, token):
	# for_update bloquea la fila hasta el commit: si el usuario recarga el retorno
	# o abre dos pestañas, la segunda espera y luego ve status == "Completed".
	request = frappe.get_doc("Integration Request", request_name, for_update=True)

	if request.status in ("Completed", "Cancelled", "Failed"):
		frappe.db.commit()
		return

	data = frappe._dict(json.loads(request.data or "{}"))
	output = frappe._dict(json.loads(request.output or "{}"))

	settings = frappe.get_single("Webpay Settings")

	try:
		result = settings.get_transaction().commit(token)
	except Exception:
		request.db_set("status", "Failed", update_modified=False)
		request.db_set("error", frappe.get_traceback(), update_modified=False)
		frappe.db.commit()
		frappe.log_error(title=f"Webpay: commit falló para {request_name}")
		return

	request.db_set("output", frappe.as_json({**output, "commit": result}), update_modified=False)

	error = validate_result(data, output, result)
	if error:
		request.db_set("status", "Failed", update_modified=False)
		request.db_set("error", error, update_modified=False)
		frappe.db.commit()
		return

	request.db_set("status", "Authorized", update_modified=False)
	frappe.db.commit()

	enroll(data)

	request.db_set("status", "Completed", update_modified=False)
	frappe.db.commit()


def validate_result(data, output, result):
	"""Deber del comercio: verificar que lo que informa Transbank coincide con lo enviado."""
	if result.get("response_code") != 0 or result.get("status") != "AUTHORIZED":
		return _("Transacción no autorizada. response_code={0} status={1}").format(
			result.get("response_code"), result.get("status")
		)

	if result.get("buy_order") != output.get("buy_order"):
		return _("La orden de compra no coincide: {0} != {1}").format(
			result.get("buy_order"), output.get("buy_order")
		)

	if result.get("session_id") != output.get("session_id"):
		return _("El session_id no coincide.")

	expected = int(round(float(data.get("amount") or 0)))
	received = int(round(float(result.get("amount") or 0)))
	if expected != received:
		return _("El monto pagado no coincide: {0} != {1}").format(received, expected)

	return None


def enroll(data):
	"""Delega en LMS. on_payment_authorized es el contrato de la app payments."""
	previous_user = frappe.session.user
	# frappe.set_user() no solo cambia session.user: tambien pisa
	# session.sid y session.data como efecto secundario (frappe/__init__.py).
	# Si no los restauramos a mano, la segunda llamada a set_user() (la que
	# "restaura" al usuario original) deja la sesión con un sid corrupto, y
	# la cookie que se manda de vuelta al navegador ya no matchea su sesión
	# real: el comprador queda deslogueado al volver del pago.
	previous_sid = frappe.local.session.sid
	previous_session_data = frappe.local.session.data
	try:
		# enroll_in_course / create_enrollment usan frappe.session.user directamente
		# (lms/lms/utils.py). Sin esto se inscribiría a Guest.
		frappe.set_user(data.payer_email)

		reference_doc = frappe.get_doc(data.reference_doctype, data.reference_docname)
		reference_doc.run_method("on_payment_authorized", "Completed")
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(
			title="Webpay: pago cobrado pero la inscripción falló",
			message=f"payment={data.get('payment')} data={frappe.as_json(data)}\n{frappe.get_traceback()}",
		)
	finally:
		frappe.set_user(previous_user)
		frappe.local.session.sid = previous_sid
		frappe.local.session.data = previous_session_data


def redirect_to_result(request_name):
	return redirect_to_url(get_url(f"/webpay-resultado?ir={request_name}"))


def redirect_to_url(url):
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = url
