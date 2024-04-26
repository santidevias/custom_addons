from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_equipment_rental = fields.Boolean(default=False,
        string="Equipment rental",
        help="Allow renting and subscription of this product."
    )
    