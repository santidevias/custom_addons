from odoo import models, fields, api


RENTAL_STATUS = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('pickup', "Reserved"),
    ('return', "Pickedup"),
    ('returned', "Returned"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"


    is_equipment_rental_order = fields.Boolean(
        string="Created In App Rental",
        compute='_compute_is_equipment_rental_order',
        store=True, precompute=True, readonly=False,
        # By default, all orders created in rental app are Rental Orders
        default=lambda self: self.env.context.get('in_equipment_rental_app'))
    equipment_rental_status = fields.Selection(
        selection=RENTAL_STATUS,
        string="Rental Status",
        compute='_compute_equipment_rental_status',
        store=True)
    has_equipment_rented_products = fields.Boolean(compute='_compute_has_equipment_rented_products')


    @api.depends(
        # 'rental_start_date',
        # 'rental_return_date',
        # 'state',
        # 'order_line.is_rental',
        'order_line.product_uom_qty',
        'order_line.qty_delivered',
        # 'order_line.qty_returned',
    )
    def _compute_equipment_rental_status(self):
        # self.next_action_date = False
        for order in self:
            if not order.is_equipment_rental_order:
                order.equipment_rental_status = False
            elif order.state != 'sale':
                order.is_equipment_rental_order = order.state
            # elif order.has_pickable_lines:
            #     order.is_equipment_rental_order = 'pickup'
            #     order.next_action_date = order.rental_start_date
            elif order.has_returnable_lines:
                order.is_equipment_rental_order = 'return'
                # order.next_action_date = order.rental_return_date
            else:
                order.is_equipment_rental_order = 'returned'
    
    @api.depends('order_line.is_equipment_rental')
    def _compute_is_equipment_rental_order(self):
        for order in self:
            # If a rental product is added in the rental app to the order, it becomes a rental order
            order.is_equipment_rental_order = order.is_equipment_rental_order or order.has_equipment_rented_products

    @api.depends('order_line.is_equipment_rental')
    def _compute_has_equipment_rented_products(self):
        for so in self:
            if so.is_equipment_rental_order:
                so.has_equipment_rented_products = any(line.is_equipment_rental for line in so.order_line)