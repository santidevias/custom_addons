{
    'name': 'Sale Renting With Suscription',
    'summary': 'Module for renting with subscription',
    'category': 'Localization',
    "version": "17.0.1.0.1",
    "license": "LGPL-3",
    'author': 'IAS Software',
    'website': 'http://www.ias.com.co/',
    'depends': [
        "sale",
        "sale_renting"
    ],
    'data': [
        'views/product_template_views.xml',
        'views/sale_order_view.xml',
        'views/sale_equipment_renting_menu.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_backend': [
            'sale_equipment_rental/static/src/**/*',
        ],
    },
    'application': True,
}
