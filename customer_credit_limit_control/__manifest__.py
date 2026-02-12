{
    "name": "Customer Credit Limit Control",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "summary": "Enforce per-customer credit limits on Sales and Invoicing",
    "author": "Xoogsadetech",
    "license": "LGPL-3",
    "depends": ["account", "sale_management"],
    "data": [
        "security/credit_limit_security.xml",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/sale_order_views.xml",
    ],
    "demo": [
        "data/demo_credit_limit.xml",
    ],
    "installable": True,
    "application": False,
    "odoo": {
        "version": "16.0"
    }
}
