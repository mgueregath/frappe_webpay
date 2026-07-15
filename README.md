### Frappe Webpay

Integración de pago Webpay Plus (Transbank) para el LMS de la Alianza
Chilena Contra la Depresión. Implementa exactamente la guía verificada en
`readme.md` (raíz del repo) — ese documento explica el *por qué* de cada
decisión de diseño; este README cubre solo cómo está instalado y qué falta
para probarlo de punta a punta.

### Por qué vive en `/workspace` (igual que `achiduach_theme`)

Este proyecto corre `apps/lms` dentro de un contenedor cuyo `frappe-bench`
**no está en un volumen** — se pierde si el contenedor se recrea. Por eso
esta app está en `/workspace/frappe_webpay` (montado al host vía
`docker-compose.yml`), instalada con
`bench get-app --soft-link /workspace/frappe_webpay` en `init.sh`, no
copiada dentro del contenedor. Regla del proyecto: nada de esto vive solo
dentro del contenedor.

### Estado actual

- DocType `Webpay Settings`, el controlador (`get_payment_url`,
  `validate_transaction_currency`, `get_transaction`), `www/webpay-checkout`,
  `www/webpay-resultado` y `api.py` (`webpay_return` + los 4 flujos de
  retorno) están implementados siguiendo `readme.md` Partes 3–8 tal cual.
- `frappe_webpay/setup.py` → `configure_integration_test_mode()` deja el
  sitio listo para probar en **Integración**: habilita CLP, desactiva
  `show_usd_equivalent`, carga las credenciales públicas de prueba de
  Transbank en `Webpay Settings`, y setea
  `LMS Settings.payment_gateway = Webpay` / `default_currency = CLP`. Se
  corre sola en `init.sh` en cada bootstrap (no está hookeada a
  `after_install`: activar una pasarela de pago, aunque sea de prueba, es
  una decisión que se toma a propósito, no un side-effect silencioso de
  instalar la app).
- Verificado con una transacción real contra el sandbox de Integración de
  Transbank (`frappe_webpay.setup.smoke_test_create`): las credenciales y
  el SDK funcionan, Transbank acepta la transacción y devuelve token +
  URL de pago. El `Integration Request` queda registrado correctamente
  (`status=Queued`, `request_id`=token, `url=https://webpay3gint.transbank.cl/...`).
- El curso demo "A guide to Frappe Learning" está marcado como
  `paid_course` a `CLP 50.000` para poder probar el cobro real.

### `return_url` actual: dominio público (túnel/proxy)

Webpay necesita alcanzar la `return_url` **desde el navegador del
comprador** después de que este termina de pagar en el sitio de Transbank.
`host_name` está seteado al dominio público que apunta (vía túnel/proxy) a
este dev:

```bash
bench --site lms.localhost set-config host_name https://achid.labs.codeffeine.io
# Sin esto, get_url() le agrega ":8000" (webserver_port) al no encontrar
# puerto explicito en host_name mientras developer_mode este prendido —
# ver la nota en init.sh junto a esta misma linea.
bench --site lms.localhost set-config restart_supervisor_on_update 1
bench --site lms.localhost clear-cache
```

Verificado: `get_url()` y `get_url("/api/method/frappe_webpay.api.webpay_return")`
ya devuelven `https://achid.labs.codeffeine.io` tal cual, sin puerto.

Antes se usó la IP de LAN de este dev (`http://10.0.0.4:8008`, sin HTTPS)
para probar desde otros equipos de la misma red sin depender de un túnel;
funcionaba porque el regreso es una navegación del navegador, no una
llamada servidor-a-servidor. Si el destino del túnel cambia, o antes de
producción, hay que volver a apuntar `host_name`:

```bash
bench --site lms.localhost set-config host_name https://<nuevo-dominio-o-tunel>
bench --site lms.localhost clear-cache
```

Con la `return_url` alcanzable, seguir la Parte 10 de `readme.md` (tarjetas
de prueba, los 10 casos a cubrir, diagnóstico vía `Integration Request`).

### Camino a producción

Ver `readme.md` Parte 12. Nada de código cambia: se edita `Webpay Settings`
(`Environment = Production`, código de comercio y Api Key reales) y el SDK
enruta solo a `https://webpay3g.transbank.cl`.

### License

mit
