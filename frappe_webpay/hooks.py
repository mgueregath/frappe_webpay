app_name = "frappe_webpay"
app_title = "Frappe Webpay"
app_publisher = "Alianza Chilena Contra la Depresion"
app_description = "Integracion de pago Webpay Plus (Transbank) para Frappe LMS"
app_email = "contacto@achiduach.cl"
app_license = "mit"

# Send non-GET requests for this app's endpoints as native `application/json`
# bodies instead of form-encoded, per-key JSON-stringified values.
use_json_request_body = True

# Apps
# ------------------

# LMS: webpay_settings.get_payment_url() is invoked by lms.lms.payments and
# writes conventions LMS expects (LMS Settings.payment_gateway, order_id).
# payments: create_payment_gateway() registers "Webpay" as a Payment Gateway.
# Neither import is optional — installing this app on a site without both
# fails at hooks-import time with an obscure ModuleNotFoundError instead of
# this explicit, checked-at-install-time message.
required_apps = ["lms", "payments"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "frappe_webpay",
# 		"logo": "/assets/frappe_webpay/logo.png",
# 		"title": "Frappe Webpay",
# 		"route": "/frappe_webpay",
# 		"has_permission": "frappe_webpay.api.permission.has_app_permission",
# 	}
# ]

# Companion apps that extend a host app (instead of taking their own apps-screen icon) can pin
# their workspaces into the host app's workspace dock (rail) with this hook.
# add_app_to_rail = [
# 	{
# 		"app": "erpnext",
# 		"workspace": "My Workspace",
# 		"has_permission": "frappe_webpay.api.permission.has_app_permission",
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/frappe_webpay/css/frappe_webpay.css"
# app_include_js = "/assets/frappe_webpay/js/frappe_webpay.js"

# include js, css files in header of web template
# web_include_css = "/assets/frappe_webpay/css/frappe_webpay.css"
# web_include_js = "/assets/frappe_webpay/js/frappe_webpay.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "frappe_webpay/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "frappe_webpay/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "frappe_webpay.utils.jinja_methods",
# 	"filters": "frappe_webpay.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "frappe_webpay.install.before_install"
# after_install = "frappe_webpay.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "frappe_webpay.uninstall.before_uninstall"
# after_uninstall = "frappe_webpay.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "frappe_webpay.utils.before_app_install"
# after_app_install = "frappe_webpay.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "frappe_webpay.utils.before_app_uninstall"
# after_app_uninstall = "frappe_webpay.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "frappe_webpay.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "frappe_webpay.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"frappe_webpay.tasks.all"
# 	],
# 	"daily": [
# 		"frappe_webpay.tasks.daily"
# 	],
# 	"hourly": [
# 		"frappe_webpay.tasks.hourly"
# 	],
# 	"weekly": [
# 		"frappe_webpay.tasks.weekly"
# 	],
# 	"monthly": [
# 		"frappe_webpay.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "frappe_webpay.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "frappe_webpay.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "frappe_webpay.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "frappe_webpay.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["frappe_webpay.utils.before_request"]
# after_request = ["frappe_webpay.utils.after_request"]

# Job Events
# ----------
# before_job = ["frappe_webpay.utils.before_job"]
# after_job = ["frappe_webpay.utils.after_job"]

# after_file_upload = ["frappe_webpay.utils.after_file_upload"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"frappe_webpay.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# Custom extension points
# ------------------------------
#
# webpay_result_branding: lets another installed app (typically a theme)
# restyle /webpay-resultado without frappe_webpay depending on it. Declare a
# dict in that app's hooks.py, e.g.:
#
#   webpay_result_branding = {
#       "container": "your-css-class",
#       "surface": "your-css-class",
#       "cta_button": "your-css-class",
#   }
#
# Any key left out keeps frappe_webpay's built-in generic style for that
# element. See frappe_webpay/www/webpay_resultado.py:get_branding and
# README.md for details. Reference implementation: achiduach_theme/hooks.py.

