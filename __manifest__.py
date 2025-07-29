# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock Card Report',
    'summary': 'Add stock card report on Inventory Reporting.',
    'version': '12.0.1.0.1',
    'category': 'Warehouse',
    'website': 'https://github.com/OCA/stock-logistics-reporting',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'stock_account',
        'stock_landed_costs',
        'date_range',
        'report_xlsx_helper',
        'abs_hide_sale_cost_price',
    ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/stock_card_report.xml',
        'wizard/stock_card_report_wizard_view.xml',
        'wizard/stock_category_wizard_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
