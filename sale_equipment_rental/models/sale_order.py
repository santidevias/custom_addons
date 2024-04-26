# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from math import ceil

from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.tools import float_compare

EQUIPMENT_RENTAL_STATUS = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('pickup', "Reserved"),
    ('return', "Pickedup"),
    ('returned', "Returned"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _sql_constraints = [(
        'rental_period_coherence',
        "CHECK(equipment_rental_start_date < equipment_rental_return_date)",
        "The rental start date must be before the rental return date if any.",
    )]

    #=== FIELDS ===#

    is_equipment_rental_order = fields.Boolean(
        string="Created In App Equipment Rental",
        compute='_compute_is_equipment_rental_order',
        store=True, precompute=True, readonly=False,
        # By default, all orders created in rental app are Rental Orders
        default=lambda self: self.env.context.get('in_equipment_rental_app'))
    has_equipment_rented_products = fields.Boolean(compute='_compute_has_equipment_rented_products')
    equipment_rental_start_date = fields.Datetime(string="Equipment Rental Start Date", tracking=True)
    equipment_rental_return_date = fields.Datetime(string="Equipment Rental Return Date", tracking=True)
    equipment_rental_return_date_required = fields.Boolean(compute='_compute_equipment_rental_return_date_required')
    equipment_duration_days = fields.Integer(
        string="Duration in days for equipment",
        compute='_compute_duration_equipment',
        help="The duration in days of the rental period.",
    )
    equipment_remaining_hours = fields.Integer(
        string="Remaining duration in hours for equipment",
        compute='_compute_duration_equipment',
        help="The leftover hours of the rental period.",
    )
    equipment_show_update_duration = fields.Boolean(string="Has Duration Changed for equipment", store=False)

    equipment_rental_status = fields.Selection(
        selection=EQUIPMENT_RENTAL_STATUS,
        string="Rental Equipment Status",
        compute='_compute_rental_equipment_status',
        store=True)
    # equipment_rental_status = next action to do basically, but shown string is action done.
    equipment_next_action_date = fields.Datetime(
        string="Next Action for equipment", compute='_compute_rental_equipment_status', store=True)

    equipment_has_pickable_lines = fields.Boolean(compute='_compute_equipment_has_action_lines')
    equipment_has_returnable_lines = fields.Boolean(compute='_compute_equipment_has_action_lines')

    equipment_is_late = fields.Boolean(
        string="Equipment is overdue",
        help="The products haven't been picked-up or returned in time",
        compute='_compute_equipment_is_late',
    )

    #=== COMPUTE METHODS ===#

    @api.depends('order_line.equipment_is_rental')
    def _compute_is_equipment_rental_order(self):
        for order in self:
            # If a rental product is added in the rental app to the order, it becomes a rental order
            order.is_equipment_rental_order = order.is_equipment_rental_order or order.has_equipment_rented_products

    @api.depends('order_line.equipment_is_rental', 'equipment_rental_start_date')
    def _compute_has_equipment_rented_products(self):
        for so in self:
            if not so.equipment_rental_start_date:
                so.has_equipment_rented_products = any(line.equipment_is_rental for line in so.order_line)
            else:
                so.has_equipment_rented_products = False
    
    @api.depends('equipment_rental_start_date', 'has_equipment_rented_products')
    def _compute_equipment_rental_return_date_required(self):
        for so in self:
            if so.has_equipment_rented_products:
                print("Vea 1: ", so.equipment_rental_return_date_required, " data_start: ", so.equipment_rental_start_date)
                if not so.equipment_rental_start_date:
                    so.equipment_rental_return_date_required = True
                else:
                    so.equipment_rental_return_date_required = False
            elif so.equipment_rental_return_date_required is None:
                print("Vea 2: ", so.equipment_rental_return_date_required)
                so.equipment_rental_return_date_required = False
                

    @api.depends('equipment_rental_start_date', 'equipment_rental_return_date')
    def _compute_duration_equipment(self):
        self.equipment_duration_days = 0
        self.equipment_remaining_hours = 0
        for order in self:
            if order.equipment_rental_start_date and order.equipment_rental_return_date:
                duration = order.equipment_rental_return_date - order.equipment_rental_start_date
                order.equipment_duration_days = duration.days
                order.equipment_remaining_hours = ceil(duration.seconds / 3600)

    @api.depends(
        'equipment_rental_start_date',
        'equipment_rental_return_date',
        'state',
        'order_line.equipment_is_rental',
        'order_line.product_uom_qty',
        'order_line.qty_delivered',
        'order_line.qty_equipment_returned',
    )
    def _compute_rental_equipment_status(self):
        self.equipment_next_action_date = False
        for order in self:
            if not order.is_equipment_rental_order:
                order.equipment_rental_status = False
            elif order.state != 'sale':
                order.equipment_rental_status = order.state
            elif order.equipment_has_pickable_lines:
                order.equipment_rental_status = 'pickup'
                order.equipment_next_action_date = order.equipment_rental_start_date
            elif order.equipment_has_returnable_lines:
                order.equipment_rental_status = 'return'
                order.equipment_next_action_date = order.equipment_rental_return_date
            else:
                order.equipment_rental_status = 'returned'

    @api.depends(
        'is_equipment_rental_order',
        'state',
        'order_line.equipment_is_rental',
        'order_line.product_uom_qty',
        'order_line.qty_delivered',
        'order_line.qty_equipment_returned',
    )
    def _compute_equipment_has_action_lines(self):
        self.equipment_has_pickable_lines = False
        self.equipment_has_returnable_lines = False
        for order in self:
            if order.state == 'sale' and order.is_equipment_rental_order:
                rental_order_lines = order.order_line.filtered('equipment_is_rental')
                order.equipment_has_pickable_lines = any(
                    sol.qty_delivered < sol.product_uom_qty for sol in rental_order_lines
                )
                order.equipment_has_returnable_lines = any(
                    sol.qty_equipment_returned < sol.qty_delivered for sol in rental_order_lines
                )

    @api.depends('is_equipment_rental_order', 'equipment_next_action_date', 'equipment_rental_status')
    def _compute_equipment_is_late(self):
        now = fields.Datetime.now()
        for order in self:
            tolerance_delay = relativedelta(hours=order.company_id.equipment_min_extra_hour)
            order.equipment_is_late = (
                order.is_equipment_rental_order
                and order.equipment_rental_status in ['pickup', 'return']  # equipment_has_pickable_lines or equipment_has_returnable_lines
                and order.equipment_next_action_date
                and order.equipment_next_action_date + tolerance_delay < now
            )

    #=== ONCHANGE METHODS ===#

    @api.onchange('equipment_rental_start_date', 'equipment_rental_return_date')
    def _onchange_duration_show_update_duration(self):
        self.equipment_show_update_duration = any(line.equipment_is_rental for line in self.order_line)

    @api.onchange('is_equipment_rental_order')
    def _onchange_is_equipment_rental_order(self):
        self.ensure_one()
        if self.is_equipment_rental_order:
            self._rental_set_dates()

    #=== ACTION METHODS ===#

    def action_update_rental_prices(self):
        self.ensure_one()
        self._recompute_rental_prices()
        self.message_post(body=_("Rental prices have been recomputed with the new period."))

    def _recompute_rental_prices(self):
        self.with_context(rental_recompute_price=True)._recompute_prices()

    def _get_update_prices_lines(self):
        """ Exclude non-rental lines from price recomputation"""
        lines = super()._get_update_prices_lines()
        if not self.env.context.get('rental_recompute_price'):
            return lines
        return lines.filtered('equipment_is_rental')

    # PICKUP / RETURN : rental.processing wizard

    def action_open_pickup(self):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lines_to_pickup = self.order_line.filtered(
            lambda r:
                r.equipment_is_rental
                and float_compare(r.product_uom_qty, r.qty_delivered, precision_digits=precision) > 0)
        return self._open_rental_wizard('pickup', lines_to_pickup.ids)

    def action_open_return(self):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        lines_to_return = self.order_line.filtered(
            lambda r:
                r.equipment_is_rental
                and float_compare(r.qty_delivered, r.qty_equipment_returned, precision_digits=precision) > 0)
        return self._open_rental_wizard('return', lines_to_return.ids)

    def _open_rental_wizard(self, status, order_line_ids):
        context = {
            'order_line_ids': order_line_ids,
            'default_status': status,
            'default_order_id': self.id,
        }
        return {
            'name': _('Validate a pickup') if status == 'pickup' else _('Validate a return'),
            'view_mode': 'form',
            'res_model': 'equipment.rental.order.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    def _get_portal_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        if self.is_equipment_rental_order:
            return self.env.ref('sale_equipment_rental.equipment_rental_order_action')
        else:
            return super()._get_portal_return_action()

    def _get_product_catalog_domain(self):
        """ Override of `_get_product_catalog_domain` to extend the domain to rental-only products.

        :returns: A list of tuples that represents a domain.
        :rtype: list
        """
        domain = super()._get_product_catalog_domain()
        if self.is_equipment_rental_order:
            return expression.OR([
                domain, [('equipment_rent_ok', '=', True), ('company_id', 'in', [self.company_id.id, False])]
            ])
        return domain

    #=== TOOLING ===#

    def _rental_set_dates(self):
        self.ensure_one()
        if self.equipment_rental_start_date and self.equipment_rental_return_date:
            return

        equipment_start_date = fields.Datetime.now().replace(minute=0, second=0) + relativedelta(hours=1)
        equipment_return_date = equipment_start_date + relativedelta(days=1)
        self.update({
            'equipment_rental_start_date': equipment_start_date,
            'equipment_rental_return_date': equipment_return_date,
        })

    #=== BUSINESS METHODS ===#

    def _get_product_catalog_order_data(self, products, **kwargs):
        """ Override to add the rental dates for the price computation """
        return super()._get_product_catalog_order_data(
            products,
            equipment_start_date=self.equipment_rental_start_date,
            end_date=self.equipment_rental_return_date,
            **kwargs,
        )

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """ Override to add the context to mark the line as rental and the rental dates for the
        price computation
        """
        if self.is_equipment_rental_order:
            self = self.with_context(in_equipment_rental_app=True)
            product = self.env['product.product'].browse(product_id)
            if product.equipment_rent_ok:
                self._rental_set_dates()
        return super()._update_order_line_info(
            product_id,
            quantity,
            equipment_start_date=self.equipment_rental_start_date,
            end_date=self.equipment_rental_return_date,
            **kwargs,
        )

    def _get_action_add_from_catalog_extra_context(self):
        """ Override to add rental dates in the context for product availabilities. """
        extra_context = super()._get_action_add_from_catalog_extra_context()
        extra_context.update(equipment_start_date=self.equipment_rental_start_date, end_date=self.equipment_rental_return_date)
        return extra_context
