from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_limit = fields.Monetary(
        string="Credit Limit",
        company_dependent=True,
        currency_field="company_currency_id",
        help="Maximum allowed credit exposure for this customer (per company). Set to 0 to disable the limit.",
    )

    credit_limit_policy = fields.Selection(
        selection=[("block", "Block"), ("warn", "Warn")],
        string="Credit Limit Policy",
        default="block",
        help="Block: prevent confirmations/posting when limit is exceeded. Warn: show warning but allow.",
    )

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Company Currency",
        compute="_compute_company_currency_id",
        readonly=True,
    )

    credit_exposure = fields.Monetary(
        string="Credit Exposure",
        currency_field="company_currency_id",
        compute="_compute_credit_limit_amounts",
        readonly=True,
        help="Current exposure used for credit limit checks (receivables + optionally uninvoiced confirmed sales).",
    )

    credit_available = fields.Monetary(
        string="Credit Available",
        currency_field="company_currency_id",
        compute="_compute_credit_limit_amounts",
        readonly=True,
        help="Remaining credit before reaching the limit.",
    )

    @api.depends_context("company")
    def _compute_company_currency_id(self):
        for partner in self:
            partner.company_currency_id = partner.env.company.currency_id

    @api.depends_context("company")
    def _compute_credit_limit_amounts(self):
        company = self.env.company
        for partner in self:
            exposure = partner._credit_limit_get_exposure(company=company)
            partner.credit_exposure = exposure
            limit = partner.with_company(company).credit_limit or 0.0
            partner.credit_available = limit - exposure

    def _credit_limit_is_enforced(self, company=None):
        self.ensure_one()
        company = company or self.env.company
        if not company.credit_limit_enforce:
            return False
        limit = self.with_company(company).credit_limit or 0.0
        return bool(limit and limit > 0.0)

    def _credit_limit_get_uninvoiced_sales_amount(self, company=None, exclude_orders=None):
        """Returns amount in company currency."""
        self.ensure_one()
        company = company or self.env.company
        exclude_orders = exclude_orders or self.env["sale.order"]

        if not company.credit_limit_include_uninvoiced_sales:
            return 0.0

        commercial = self.commercial_partner_id
        domain = [
            ("company_id", "=", company.id),
            ("state", "in", ["sale", "done"]),
            ("partner_id", "child_of", commercial.id),
        ]
        if exclude_orders:
            domain.append(("id", "not in", exclude_orders.ids))

        orders = self.env["sale.order"].search(domain)
        total = 0.0
        for order in orders:
            remaining = (order.amount_total - getattr(order, "amount_invoiced", 0.0))
            if remaining <= 0:
                continue
            if order.currency_id == company.currency_id:
                total += remaining
            else:
                total += order.currency_id._convert(
                    remaining,
                    company.currency_id,
                    company,
                    order.date_order or fields.Date.context_today(order),
                )
        return total

    def _credit_limit_get_receivables_amount(self, company=None):
        """Uses Odoo's computed receivables (partner.credit) in company currency."""
        self.ensure_one()
        company = company or self.env.company
        commercial = self.commercial_partner_id.with_company(company)
        return commercial.credit or 0.0

    def _credit_limit_get_exposure(self, company=None, exclude_orders=None):
        self.ensure_one()
        company = company or self.env.company
        receivables = self._credit_limit_get_receivables_amount(company=company)
        uninvoiced_sales = self._credit_limit_get_uninvoiced_sales_amount(
            company=company,
            exclude_orders=exclude_orders,
        )
        return receivables + uninvoiced_sales

    def _credit_limit_check_or_raise(self, delta_amount=0.0, company=None, exclude_orders=None):
        """delta_amount: additional exposure to add (company currency)."""
        self.ensure_one()
        company = company or self.env.company

        if not self._credit_limit_is_enforced(company=company):
            return

        limit = self.with_company(company).credit_limit or 0.0
        exposure = self._credit_limit_get_exposure(company=company, exclude_orders=exclude_orders)
        projected = exposure + (delta_amount or 0.0)
        if projected <= limit:
            return

        available = limit - exposure
        message = _(
            "Credit limit exceeded for %(partner)s.\n"
            "Limit: %(limit).2f\n"
            "Current exposure: %(exposure).2f\n"
            "This document adds: %(delta).2f\n"
            "Available before this document: %(available).2f\n"
            "Projected exposure: %(projected).2f",
            partner=self.display_name,
            limit=limit,
            exposure=exposure,
            delta=delta_amount or 0.0,
            available=available,
            projected=projected,
        )

        if self.credit_limit_policy == "warn":
            return {"warning": message}

        raise UserError(message)
