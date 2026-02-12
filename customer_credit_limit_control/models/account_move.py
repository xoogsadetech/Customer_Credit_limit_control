from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _credit_limit_delta_company_currency(self):
        self.ensure_one()
        # amount_total_signed is in company currency and includes sign.
        return self.amount_total_signed or 0.0

    def action_post(self):
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                continue
            if not move.partner_id:
                continue

            company = move.company_id
            partner = move.partner_id.commercial_partner_id

            if not partner._credit_limit_is_enforced(company=company):
                continue

            if self.env.user.has_group("customer_credit_limit_control.group_credit_limit_manager"):
                continue

            delta = move._credit_limit_delta_company_currency()
            # Refunds reduce exposure; no need to block.
            if delta <= 0:
                continue

            warning = partner._credit_limit_check_or_raise(delta_amount=delta, company=company)
            if warning and isinstance(warning, dict) and warning.get("warning"):
                move.message_post(body=_("Credit limit warning:\n%s") % warning["warning"])

        return super().action_post()
