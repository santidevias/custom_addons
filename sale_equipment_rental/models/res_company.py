# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # RENTAL company defaults :

    # Extra Costs

    equipment_extra_hour = fields.Float("Per Hour (Equipment)", default=0.0)
    equipment_extra_day = fields.Float("Per Day (Equipment)", default=0.0)
    equipment_min_extra_hour = fields.Integer("Minimum delay time before applying fines. (Equipment)", default=2)

    equipment_extra_product = fields.Many2one(
        'product.product', string="Product (Equipment)",
        help="The product is used to add the cost to the sales order",
        domain="[('type', '=', 'service')]")

    _sql_constraints = [
        ('equipment_min_extra_hour',
            "CHECK(equipment_min_extra_hour >= 1)",
            "Minimal delay time before applying fines has to be positive."),
    ]
