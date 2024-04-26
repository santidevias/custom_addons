# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # RENTAL company defaults :

    # Extra Costs

    equipment_extra_hour = fields.Float(
        "Per Hour (Equipment)", related="company_id.equipment_extra_hour", readonly=False,
        help="This is the default extra cost per hour set on newly created products. You can change this value for existing products directly on the product itself.")
    equipment_extra_day = fields.Float(
        "Per Day (Equipment)", related="company_id.equipment_extra_day", readonly=False,
        help="This is the default extra cost per day set on newly created products. You can change this value for existing products directly on the product itself.")
    # extra_week = fields.Monetary("Extra Week")
    equipment_min_extra_hour = fields.Integer("Minimum delay time before applying fines. (Equipment)", related="company_id.equipment_min_extra_hour", readonly=False)
    # week uom disabled in rental for the moment
    equipment_extra_product = fields.Many2one(
        'product.product', string="Delay Product (Equipment)",
        help="This product will be used to add fines in the Rental Order.", related="company_id.equipment_extra_product",
        readonly=False, domain="[('type', '=', 'service')]")

    module_sale_renting_sign = fields.Boolean(string="Digital Documents (Equipment)")

    @api.onchange('equipment_extra_hour')
    def _onchange_extra_hour_for_equipment(self):
        self.env['ir.property']._set_default("equipment_extra_hourly", "product.template", self.equipment_extra_hour)

    @api.onchange('equipment_extra_day')
    def _onchange_extra_day_for_equipment(self):
        self.env['ir.property']._set_default("equipment_extra_daily", "product.template", self.equipment_extra_day)
