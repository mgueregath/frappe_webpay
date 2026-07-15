### Frappe Webpay

Integración de pago **Webpay Plus** (Transbank) para **Frappe LMS**. Se
instala como una app más de Frappe: agrega "Webpay" como Payment Gateway
para que LMS lo ofrezca en el checkout de cursos pagados.

Para el detalle de diseño y el paso a paso de cómo se construyó esta app
desde cero, ver `readme.md` en la raíz del repo. Este documento cubre solo
cómo instalarla y configurarla en tu propia instancia.

### Requisitos

- Un sitio Frappe con las apps `lms` y `payments` instaladas (declaradas en
  `required_apps`, `bench install-app` falla con un mensaje claro si faltan).
- Cuenta de comercio Webpay Plus en Transbank (para producción). Para
  probar, Transbank publica credenciales de Integración públicas que esta
  app ya trae incorporadas — ver más abajo.

### Instalación

```bash
bench get-app https://github.com/mgueregath/frappe_webpay.git
bench --site <tu-sitio> install-app frappe_webpay
```

(Para desarrollo local con la app montada desde el host en vez de copiada
dentro del contenedor: `bench get-app --soft-link /ruta/a/frappe_webpay`.)

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

Si prefieres dejar un sitio nuevo listo de un solo comando (credenciales de
Integración + CLP habilitado + `LMS Settings.payment_gateway = Webpay`):

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

Con eso alcanzable, sigue la Parte 10 de `readme.md` (tarjetas de prueba,
los casos a cubrir, diagnóstico vía `Integration Request`).

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
`achiduach_theme/hooks.py` de este mismo repo.

### Camino a producción

Ver `readme.md` Parte 12 para el detalle. En resumen: `Environment =
Production` y las credenciales reales en `Webpay Settings`, nada más.

### License

MIT

---

Desarrollado por [Codeffeine](https://codeffeine.io)

<img src="docs/images/codeffeine-logo.png" alt="Codeffeine" width="180">

