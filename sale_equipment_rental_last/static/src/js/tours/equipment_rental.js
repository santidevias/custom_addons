/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

import { markup } from "@odoo/owl";

registry.category("web_tour.tours").add('equipment_rental_tour', {
    url: "/web",
    sequence: 250,
    steps: () => [stepUtils.showAppsMenuItem(), {
        trigger: '.o_app[data-menu-xmlid="sale_equipment_rental.equipment_rental_menu_root"]',
        content: markup(_t("Want to <b>equipment rent products</b>? \n Let's discover IAS Equipment Rental App.")),
        position: 'bottom',
    }]
})