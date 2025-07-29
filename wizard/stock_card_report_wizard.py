from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import UserError


class StockCardReportWizard(models.TransientModel):
    _name = 'stock.card.report.wizard'
    _description = 'Stock Card Report Wizard'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Period',
    )
    date_from = fields.Date(
        string='Start Date',
    )
    date_to = fields.Date(
        string='End Date',
    )
    warehouse_ids = fields.Many2many('stock.warehouse', 'wh_card_wiz_rel', 'wh', 'wiz', string='Bodegas', )
    location_ids = fields.Many2many(
        comodel_name='stock.location',
        string='Locations',
        domain="[('id', 'in', filter_location_ids)]",
    )

    @api.multi
    @api.depends("warehouse_ids", "allow_virtual_locations")
    def _compute_filter_locations(self):
        for record in self:
            domain = []
            if not record.allow_virtual_locations:
                domain = [('usage', 'in', ('internal', 'transit'))]
            locations = self.env["stock.location"].search(domain)
            if self.warehouse_ids:
                locations = locations.filtered(
                     lambda l: l.get_warehouse().id in self.warehouse_ids.ids
            )
            record.filter_location_ids = locations

    filter_location_ids = fields.Many2many(
        comodel_name='stock.location',
        string='Locations',
        help="Technical field to filter locations to show",
        compute=_compute_filter_locations,
    )

    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        domain="[('type','=','product')]",
        required=False,
    )
    code_from = fields.Char("Code from", size=1, )
    code_to = fields.Char("Code to", size=1, )
    categ_ids = fields.Many2many(
        comodel_name='product.category',
        string='Products Category',
    )
    sku_type = fields.Selection([
            ('code','Código'),
            ('barcode','Código de barras'),
        ], default="code",
        string='Tipo de código',
    )

    def action_open_category_selector(self):
            return {
                'name': 'Select Categories',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.card.select.category.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_wizard_id': self.id
                }
            }


    @api.multi
    @api.depends('product_ids', 'categ_ids')
    def _compute_filter_lot_ids(self):
        for record in self:
            products = record.product_ids
            products += self.env['product.product'].search([('categ_id','in', record.categ_ids.ids)])
            lots = self.env['stock.production.lot'].search([('product_id', 'in', products.ids)])
            record.filter_lot_ids = lots

    filter_lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string='Filter Product Lots',
        compute=_compute_filter_lot_ids,
    )

    lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string='Product Lots',
        domain="[('id', 'in', filter_lot_ids)]"
    )


    allow_virtual_locations = fields.Boolean(string="Allow virtual locations", )
    consolidated = fields.Boolean(string='Consolidated Report?', )
    group_by_lot = fields.Boolean(string='Group by lot')
    group_by_location = fields.Boolean(string='Group by location')
    show_lot = fields.Boolean(string='Show Lot', )
    show_partner = fields.Boolean(string='Show Partner', )
    include_sublocations = fields.Boolean(string='Include sublocations', )
    only_accounted_moves = fields.Boolean(string='Only Accounted Moves', )

    @api.onchange('show_lot', 'lot_ids')
    def _onchange_lot_ids(self):
        if self.lot_ids:
            self.show_lot = True

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'stock_card_report.action_report_stock_card_report_html')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_stock_card_report(self):
        self.ensure_one()

        if not self.product_ids and not self.categ_ids and not self.code_from and not self.code_to:
            raise UserError(_("Select some products, categories or code range"))

        return {
            'date_from': self.date_from or "2000-01-01",
            'date_to': self.date_to or fields.Date.context_today(self),
            'code_from': self.code_from,
            'code_to': self.code_to,
            'product_ids': [(6, 0, self.product_ids.ids)],
            'warehouse_ids': [(6, 0, self.warehouse_ids.ids)],
            'location_ids': [(6, 0, self.location_ids.ids)],
            'categ_ids': [(6, 0, self.categ_ids.ids)],
            'consolidated': self.consolidated,
            'group_by_lot': self.group_by_lot,
            'group_by_location': self.group_by_location,
            'show_lot': self.show_lot,
            'show_partner': self.show_partner,
            'include_sublocations': self.include_sublocations,
            'lot_ids': [(6, 0, self.lot_ids.ids)],
            'only_accounted_moves': self.only_accounted_moves,
            'sku_type': self.sku_type,
        }

    def _export(self, report_type):
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)

