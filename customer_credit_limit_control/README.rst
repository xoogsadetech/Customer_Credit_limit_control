Customer Credit Limit Control
=============================

Features
--------

- Define a per-customer (per company) credit limit on Contacts.
- Optionally include confirmed but not fully invoiced Sales Orders into the exposure.
- Block Sales Order confirmation and Customer Invoice posting when the limit would be exceeded.
- Policy can be set per customer: Block or Warn.
- A "Credit Limit Manager" group can bypass blocking.

Configuration
-------------

1) Company

- Settings > Companies > (open your company)
- Enable "Enforce Customer Credit Limits"
- Optionally enable "Include Uninvoiced Sales"

2) Customer

- Contacts > (open customer) > Accounting tab
- Set "Credit Limit" and "Credit Limit Policy"

Notes
-----

- Exposure is computed as: current receivables (partner.credit) + (optional) uninvoiced confirmed sales.
- A limit of 0 disables enforcement for that customer.
