from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_limit_warning_message = fields.Char(
        string="Credit Limit Warning",
        compute="_compute_credit_limit_warning_message",
        store=False,
    )

    def _credit_limit_delta_company_currency(self):
        self.ensure_one()
        company = self.company_id
        amount = self.amount_total
        if self.currency_id == company.currency_id:
            return amount
        return self.currency_id._convert(
            amount,
            company.currency_id,
            company,
            self.date_order or fields.Date.context_today(self),
        )

    @api.depends('partner_id', 'amount_total')
    def _compute_credit_limit_warning_message(self):
        for order in self:
            warning = order._credit_limit_check()
            if warning and isinstance(warning, dict) and warning.get("warning"):
                order.credit_limit_warning_message = warning["warning"]
            else:
                order.credit_limit_warning_message = False

        if self.env.user.has_group("customer_credit_limit_control.group_credit_limit_manager"):
            return None

        delta = self._credit_limit_delta_company_currency()
        return partner._credit_limit_check_or_raise(
            delta_amount=delta,
            company=company,
            exclude_orders=self,
        )

    def action_confirm(self):
        for order in self:
            warning = order._credit_limit_check()
            if warning and isinstance(warning, dict) and warning.get("warning"):
                order.message_post(body=_("Credit limit warning:\n%s") % warning["warning"])
        return super().action_confirm()

    @api.onchange("partner_id")
    def _onchange_partner_credit_limit(self):
        if not self.partner_id:
            return

        partner = self.partner_id.commercial_partner_id
        company = self.company_id or self.env.company
        if not partner._credit_limit_is_enforced(company=company):
            return

        if partner.credit_limit_policy != "warn":
            return

        # For onchange, give a heads-up without blocking.
        delta = self._credit_limit_delta_company_currency() if self.amount_total else 0.0
        res = partner._credit_limit_check_or_raise(
            delta_amount=delta,
            company=company,
            exclude_orders=self,
        )
        if res and isinstance(res, dict) and res.get("warning"):
            return {
                "warning": {
                    "title": _("Credit Limit"),
                    "message": res["warning"],
                }
            }
