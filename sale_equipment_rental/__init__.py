# -*- coding: utf-8 -*-

from . import models
from . import populate
from . import wizard
from . import report
from odoo.tools.sql import column_exists

def _pre_init_rental(env):
    """ Allow installing sale_renting in databases with large sale.order / sale.order.line tables.
    The different rental fields are all NULL (falsy) for existing sale orders,
    the computation is way more efficient in SQL than in Python.
    """
    if not column_exists(env.cr, 'sale_order', 'equipment_rental_status'):
        env.cr.execute("""
            ALTER TABLE "sale_order"
            ADD COLUMN "equipment_rental_start_date" timestamp,
            ADD COLUMN "equipment_rental_return_date" timestamp,
            ADD COLUMN "equipment_rental_status" VARCHAR,
            ADD COLUMN "equipment_next_action_date" timestamp
        """)
        env.cr.execute("""
            ALTER TABLE "sale_order_line"
            ADD COLUMN "equipment_reservation_begin" timestamp
        """)
