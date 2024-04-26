from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    is_equipment_rental = fields.Boolean(compute='_compute_is_equipment_rental', store=True, precompute=True)
    is_product_equipment_rentable = fields.Boolean(related='product_id.is_equipment_rental', depends=['product_id'])


    @api.depends('product_id')
    def _compute_is_equipment_rental(self):
        for line in self:
            line.is_equipment_rental = line.is_product_equipment_rentable and line.env.context.get('in_equipment_rental_app')