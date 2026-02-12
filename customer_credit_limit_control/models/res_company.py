from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    credit_limit_enforce = fields.Boolean(
        string="Enforce Customer Credit Limits",
        default=False,
        help="If enabled, customer credit limits can block Sales Order confirmations and Customer Invoice posting.",
    )

    credit_limit_include_uninvoiced_sales = fields.Boolean(
        string="Include Uninvoiced Sales",
        default=True,
        help="If enabled, the credit exposure also includes confirmed Sales Orders that are not fully invoiced.",
    )
