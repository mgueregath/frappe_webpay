### Frappe Webpay

Integración de pago **Webpay Plus** (Transbank) para **Frappe LMS**. Se
instala como una app más de Frappe: agrega "Webpay" como Payment Gateway
para que LMS lo ofrezca en el checkout de cursos pagados.

Este documento es autocontenido: cubre instalación, configuración,
arquitectura interna, pruebas y producción, sin depender de ningún otro
repo.

### Índice

- [Cómo funciona](#cómo-funciona)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Preparar el sitio](#preparar-el-sitio)
- [Configurar credenciales](#configurar-credenciales-sin-tocar-código)
- [`return_url` alcanzable](#return_url-alcanzable-desde-el-navegador-del-comprador)
- [Los 4 flujos de retorno](#los-4-flujos-de-retorno)
- [Por qué el orden de `enroll()` importa](#por-qué-el-orden-de-enroll-importa)
- [Limitación conocida (heredada de LMS)](#limitación-conocida-heredada-de-lms)
- [Personalizar la página de resultado](#personalizar-la-apariencia-de-la-página-de-resultado)
- [Probar](#probar)
- [Checklist de trampas](#checklist-de-trampas)
- [Camino a producción](#camino-a-producción)
- [Referencias](#referencias)

---

### Cómo funciona

```
Comprador en LMS ("Comprar curso")
        │
        ▼
LMS llama Webpay Settings.get_payment_url(amount, reference_doctype, ...)
        │  crea un Integration Request (service="Webpay", status Queued)
        │  crea la transacción en Transbank → token + url
        ▼
GET /webpay-checkout?ir=<IR>
        │  arma un <form method="post"> con token_ws y lo auto-envía
        ▼
POST al formulario de pago de Transbank (fuera de tu sitio)
        │  el comprador paga (o cancela, o se le vence el tiempo)
        ▼
Transbank redirige el navegador de vuelta a:
GET/POST /api/method/frappe_webpay.api.webpay_return
        │  4 flujos posibles (ver más abajo) → localiza el Integration Request
        │  si corresponde, confirma (commit) la transacción con Transbank
        │  valida que lo confirmado coincida con lo enviado
        │  si aprueba: reference_doc.run_method("on_payment_authorized", "Completed")
        ▼
Redirect a /webpay-resultado?ir=<IR>
        │  lee el Integration Request y muestra aprobado/rechazado/cancelado
        ▼
Comprador ve el resultado y vuelve al curso
```

Piezas del lado de `frappe_webpay`:

| Archivo | Rol |
| --- | --- |
| [`frappe_webpay/doctype/webpay_settings/webpay_settings.py`](frappe_webpay/frappe_webpay/doctype/webpay_settings/webpay_settings.py) | Config (credenciales, ambiente) + `get_payment_url()`, el punto de entrada que llama LMS |
| [`frappe_webpay/api.py`](frappe_webpay/api.py) | `webpay_return`, el endpoint al que Transbank redirige al comprador |
| [`frappe_webpay/www/webpay-checkout.html`](frappe_webpay/www/webpay-checkout.html) + `.py` | Página intermedia que reenvía el `token_ws` a Transbank por POST |
| [`frappe_webpay/www/webpay-resultado.html`](frappe_webpay/www/webpay-resultado.html) + `.py` | Página de resultado que ve el comprador |

Todo el estado de una transacción vive en un `Integration Request`
(`integration_request_service = "Webpay"`) — no hay una tabla propia. Sus
estados: `Queued` → `Authorized` → `Completed`, o `Cancelled`/`Failed` en
cualquier punto.

### Requisitos

- Un sitio Frappe con las apps `lms` y `payments` instaladas (declaradas en
  `required_apps` de [`hooks.py`](frappe_webpay/hooks.py); `bench
  install-app` falla con un mensaje claro si faltan, en vez de un
  `ModuleNotFoundError` oscuro al primer request).
- Cuenta de comercio Webpay Plus en Transbank (solo para producción). Para
  probar, Transbank publica credenciales de Integración públicas que esta
  app ya trae incorporadas — ver [Configurar credenciales](#configurar-credenciales-sin-tocar-código).
- Webpay Plus solo opera en **CLP**. Si tu LMS vende en otra moneda,
  necesitas otra pasarela para esos cursos.

### Instalación

```bash
bench get-app https://github.com/mgueregath/frappe_webpay.git
bench --site <tu-sitio> install-app frappe_webpay
```

(Para desarrollo local con la app montada desde el host en vez de copiada
dentro del contenedor: `bench get-app --soft-link /ruta/a/frappe_webpay`.)

### Preparar el sitio

Tres ajustes de `lms`/`frappe` que, si se saltan, la integración falla **en
silencio** (el pago nunca llega a crear la transacción, o Transbank la
rechaza porque el monto llega en otra moneda). No son de `frappe_webpay`,
son de tu sitio LMS:

1. **Moneda CLP habilitada.** En `/app/currency`, busca `CLP` y confirma
   que esté `Enabled`. Si no existe, créala.

2. **Desactivar la conversión automática a USD.** `lms.lms.utils.check_multicurrency`
   convierte el precio a USD si `LMS Settings.show_usd_equivalent` está
   activo y el país del comprador no está en `Exception Country` — y
   `validate_transaction_currency()` de esta app rechaza cualquier moneda
   que no sea CLP. En `/app/lms-settings`, elige una de las dos:
   - Desmarcar `Show USD Equivalent` (recomendado si solo vendes en un
     país con moneda CLP), o
   - Dejarlo marcado y agregar tu país a `Exception Country`.

3. **Cursos pagados en CLP, sin equivalente USD.** En cada `LMS Course`
   que quieras cobrar: `Paid Course` ✓, `Currency = CLP`, y **`Amount
   USD` vacío** (si tiene valor, `check_multicurrency` devuelve USD
   directamente, sin mirar `show_usd_equivalent`).

El comando de la siguiente sección (`configure_integration_test_mode`)
resuelve los puntos 1 y 2 automáticamente si prefieres no tocarlos a mano.

### Configurar credenciales (sin tocar código)

Todo se configura desde `/app/webpay-settings` (DocType singleton `Webpay
Settings`), no hay nada hardcodeado en el código que dependa del sitio:

- **Para probar (ambiente de Integración):** abre `/app/webpay-settings` y
  presiona el botón **"Usar credenciales públicas de prueba
  (Integración)"**. Llena `Commerce Code` y `Api Key Secret` con las
  credenciales que Transbank publica para todos los comercios en ese
  ambiente (no son secretas, solo sirven contra
  `webpay3gint.transbank.cl`). Marca `Enabled`.
- **Para producción:** cambia `Environment` a `Production` e ingresa el
  `Commerce Code` y `Api Key Secret` reales de tu cuenta Transbank. Nada de
  código cambia — el SDK enruta solo a `https://webpay3g.transbank.cl`.

Al guardar, `on_update()` corre `create_payment_gateway("Webpay",
settings="Webpay Settings")` — verifica en `/app/payment-gateway` que
exista el registro `Webpay`. Luego, en `/app/lms-settings` → pestaña
**Payment Settings**: `Payment Gateway = Webpay`, `Default Currency = CLP`.
Si el selector de `Payment Gateway` sale vacío, entra una vez al portal LMS
(Settings → Payment) para que `check_payments_app()` termine de convertir
ese campo de `Data` a `Link`, y recarga.

Si prefieres dejar un sitio nuevo listo de un solo comando (los 3 ajustes
de arriba + credenciales de Integración + gateway seleccionado en LMS):

```bash
bench --site <tu-sitio> execute frappe_webpay.setup.configure_integration_test_mode
```

### `return_url` alcanzable desde el navegador del comprador

Webpay redirige el navegador del comprador de vuelta a tu sitio después del
pago, así que `host_name` debe ser una URL pública (HTTPS) alcanzable desde
afuera — no `localhost` ni una IP privada, salvo que estés probando desde la
misma red:

```bash
bench --site <tu-sitio> set-config host_name https://tu-dominio-publico
bench --site <tu-sitio> clear-cache
```

### Los 4 flujos de retorno

Transbank redirige a `/api/method/frappe_webpay.api.webpay_return`
(`webpay_return()` en [`api.py`](frappe_webpay/api.py)) con parámetros
distintos según qué pasó, y el endpoint tiene que distinguirlos sin poder
confiar en la sesión del navegador (el retorno es `allow_guest=True`
porque el flujo de anulación en Integración llega por **POST cross-site**,
y las cookies `SameSite=Lax` de Frappe no viajan en ese caso):

| Flujo | Llega | Método | Acción |
| --- | --- | --- | --- |
| Normal (aprobado o rechazado) | `token_ws` | GET | `commit_transaction()`: confirma con Transbank y valida el resultado |
| Timeout del formulario (10 min en Integración, 4 en producción) | `TBK_ORDEN_COMPRA`, `TBK_ID_SESION` — **sin token** | GET | `close(..., "Cancelled")`, no hay nada que confirmar |
| Usuario anula ("Anular compra") | `TBK_TOKEN`, `TBK_ORDEN_COMPRA`, `TBK_ID_SESION` | **POST en Integración**, GET en producción | `close(..., "Cancelled")` |
| Error en el formulario + "volver al sitio" | `token_ws` **y** `TBK_TOKEN` + los otros dos | GET | Si llega `TBK_TOKEN`, se trata como anulado — no se confirma aunque también venga `token_ws` |

`resolve_request()` localiza el `Integration Request` por `request_id`
(el token) y, si no hay token (timeout), por el `buy_order` — que se
construyó como `f"lms-{integration_request.name}"` al crear la
transacción, así que siempre es recuperable aunque Transbank nunca haya
devuelto un token.

`commit_transaction()` toma el documento con `for_update=True`: si el
comprador recarga la página de retorno o abre dos pestañas, la segunda
consulta espera el lock y luego encuentra `status == "Completed"` sin
volver a confirmar ni cobrar dos veces. `validate_result()` es el deber
del comercio ante Transbank: verificar que `response_code`, `buy_order`,
`session_id` y el monto que informa Transbank coincidan exactamente con lo
que se envió al crear la transacción — cualquier discrepancia marca la
transacción como `Failed` aunque Transbank la haya dado por aprobada.

### Por qué el orden de `enroll()` importa

`enroll()` no marca nada como pagado directamente. Llama
`reference_doc.run_method("on_payment_authorized", "Completed")`, que en
LMS (`LMSCourse`/`LMSBatch`) termina en `update_payment_record()`, la cual:

1. Busca el `Integration Request` más reciente con ese
   `reference_doctype`/`reference_docname` **y `owner = frappe.session.user`**.
2. Lee su `data` y marca `LMS Payment.payment_received = 1`, `payment_id`,
   `order_id`.
3. Llama a `complete_enrollment(...)`.

De ahí salen tres requisitos no obvios que el código de esta app cumple a
propósito:

- El IR debe tener **`owner` = el comprador** — se cumple porque
  `create_request_log()` corre en la sesión del comprador, al momento de
  iniciar el pago.
- El retorno debe hacer **`frappe.set_user(payer_email)`** antes de
  llamar `on_payment_authorized` — si no, el filtro por `owner` no
  encuentra nada y el pago queda huérfano (cobrado pero sin inscripción).
  `set_user()` también pisa `session.sid`/`session.data` como efecto
  secundario, así que `enroll()` los guarda y restaura a mano al volver a
  `frappe.set_user(previous_user)` — sin eso, el comprador queda
  deslogueado al volver del pago (la cookie que recibe el navegador ya no
  coincide con su sesión real).
- El `data` del IR debe traer **`order_id`** — si no,
  `LMS Payment.payment_id` queda nulo.

Marcar `Authorized` antes de inscribir y `Completed` después dejar una
huella clara en la base: un IR en `Authorized` significa *cobrado pero no
inscrito* — el estado a mirar primero si algo se corta a mitad de camino
(ver `frappe.log_error`, título "Webpay: pago cobrado pero la inscripción
falló").

### Limitación conocida (heredada de LMS)

`update_payment_record` toma el IR **más reciente** por `(doctype,
docname, owner)`, sin filtrar por estado. Si el mismo usuario abre dos
pestañas para el mismo curso y paga la primera después de haber iniciado
la segunda, LMS puede asociar el pago al `LMS Payment` equivocado. Esto
afecta igual a Razorpay y Stripe — es una limitación del framework LMS, no
de esta app. Si te importa, en `enroll()` puedes reemplazar el
`run_method` por una llamada directa y determinista:

```python
from lms.lms.utils import complete_enrollment, update_payment_details
update_payment_details(data)
complete_enrollment(data.payment, data.reference_doctype, data.reference_docname)
```

Es determinista, pero acopla `frappe_webpay` a las internas de `lms` en
vez de al contrato genérico `on_payment_authorized` de la app `payments`
— por eso no es el default.

### Personalizar la apariencia de la página de resultado

`/webpay-resultado` (la página que ve el comprador tras pagar) trae un
estilo genérico propio, autocontenido — funciona igual en cualquier
instancia de Frappe LMS sin depender de ningún theme.

Si tu instancia tiene un theme propio y quieres que esa página use sus
clases CSS en vez del estilo genérico, declara el hook
`webpay_result_branding` en el `hooks.py` de tu theme:

```python
webpay_result_branding = {
    "container": "tu-clase-css",
    "surface": "tu-clase-css",
    "cta_button": "tu-clase-css",
}
```

Cualquier clave que omitas conserva el estilo genérico de `frappe_webpay`
para ese elemento. `frappe_webpay` no depende de ningún theme — es el theme
el que opta por personalizar esta página. Referencia real de esto en
`hooks.py` del repo `achiduach_theme` (theme de Alianza Chilena Contra la
Depresión, un repo aparte, no incluido en este).

### Probar

**Tarjetas de prueba** (solo ambiente de Integración):

| Tarjeta | Número | CVV | Resultado |
| --- | --- | --- | --- |
| VISA | 4051 8856 0044 6623 | 123 | **Aprobada** |
| MASTERCARD | 5186 0595 5959 0568 | 123 | **Rechazada** |
| AMEX | 3700 0000 0002 032 | 1234 | Aprobada |
| Redcompra (débito) | 4051 8842 3993 7763 | — | Aprobada |
| Redcompra (débito) | 5186 0085 4123 3829 | — | Rechazada |
| Prepago VISA | 4051 8860 0005 6590 | 123 | Aprobada |

Fecha de expiración: cualquiera futura. En la pantalla de autenticación
bancaria: RUT `11.111.111-1`, clave `123`.

**Casos a cubrir** (los cuatro flujos de retorno, más los bordes reales que
rompen integraciones de pago):

| # | Caso | Cómo | Esperado |
| --- | --- | --- | --- |
| 1 | Pago aprobado | VISA 4051…6623 | IR `Completed`, inscripción creada, voucher visible |
| 2 | Pago rechazado | MASTERCARD 5186…0568 | IR `Failed`, sin inscripción, página de rechazo |
| 3 | Usuario anula | Botón "Anular compra" | IR `Cancelled`, sin inscripción. Llega por POST — no debe explotar |
| 4 | Timeout | Esperar >10 min en el formulario | IR `Cancelled`, llegan solo `TBK_ORDEN_COMPRA` y `TBK_ID_SESION` |
| 5 | Retorno repetido | Volver atrás y recargar el retorno | La segunda vez no cobra ni inscribe dos veces |
| 6 | Token vencido | Dejar `/webpay-checkout` abierto >5 min y enviar | IR `Failed`, error controlado, no traceback crudo |
| 7 | Monto alterado | Editar `data.amount` del IR a mano antes de confirmar | `validate_result` rechaza, IR `Failed` |
| 8 | Orden inexistente | `GET /api/method/frappe_webpay.api.webpay_return?token_ws=basura` | Redirige a "desconocido", no lanza 500 |
| 9 | Doble pestaña | Iniciar dos pagos del mismo curso, pagar la primera después de la segunda | Ver [Limitación conocida](#limitación-conocida-heredada-de-lms) |
| 10 | Moneda incorrecta | Poner el curso en otra moneda | `validate_transaction_currency` lanza antes de crear la transacción |

**Diagnóstico:**

```bash
bench --site <tu-sitio> console
```
```python
frappe.get_all("Integration Request",
    filters={"integration_request_service": "Webpay"},
    fields=["name", "status", "request_id", "reference_docname", "owner", "creation"],
    order_by="creation desc", limit=10)
```

Errores en `/app/error-log`. Para consultar el estado en Transbank sin
confirmar (reconciliación, sirve hasta 7 días después):

```python
frappe.get_single("Webpay Settings").get_transaction().status("<token>")
```

### Checklist de trampas

- [ ] `show_usd_equivalent` desactivado, o tu país en `exception_country`
- [ ] `Amount USD` vacío en el curso
- [ ] `CLP` habilitada en `/app/currency`
- [ ] `host_name` apunta a una URL pública HTTPS alcanzable desde el navegador del comprador
- [ ] Existe el registro `Payment Gateway = Webpay` en `/app/payment-gateway`
- [ ] `LMS Settings.payment_gateway = Webpay` y `default_currency = CLP`
- [ ] `data["order_id"]` está presente en el `Integration Request`
- [ ] Ningún estado de IR usa valores fuera de `Queued/Authorized/Completed/Cancelled/Failed`

### Camino a producción

En el código no cambia nada: `Environment = Production` y las credenciales
reales en `Webpay Settings` bastan — `get_transaction()` enruta solo a
`https://webpay3g.transbank.cl`. Lo que sí toma tiempo es conseguir esas
credenciales, porque es un trámite con Transbank, no algo de la app:

1. **Afiliarte como comercio** en `publico.transbank.cl` (Transbank solo
   certifica integraciones de comercios ya afiliados).
2. Pasar la **validación técnica**: enviar evidencia de las transacciones
   de prueba (órdenes de compra, fecha/hora) por su formulario online, más
   el logo de la tienda (GIF/PNG 130×59px).
3. Transbank aprueba y entrega la Api Key Secret productiva.
4. Hacer la **compra real de $50** de validación final.
5. Tener **HTTPS con certificado válido** en el dominio de producción (el
   `host_name` de prueba, si era un túnel, ya no sirve).

Para cursos con cobro único, Webpay Plus estándar es el producto correcto.
Oneclick y Patpass requieren un modelo de mandatos/suscripciones que LMS no
implementa.

### Referencias

- Cómo empezar, ambientes y credenciales: https://www.transbankdevelopers.cl/documentacion/como_empezar
- Webpay Plus (flujos, create, commit, status): https://www.transbankdevelopers.cl/documentacion/webpay-plus
- SDK Python: https://github.com/TransbankDevelopers/transbank-sdk-python
- App `payments` (contrato de gateways, `on_payment_authorized`): https://github.com/frappe/payments
- LMS, flujo de pago: `lms/lms/payments.py`, `lms/lms/utils.py` (`update_payment_record`, `check_multicurrency`)

### License

MIT

---

Desarrollado por [Codeffeine](https://codeffeine.io)

<img src="docs/images/codeffeine-logo.png" alt="Codeffeine" width="180">
