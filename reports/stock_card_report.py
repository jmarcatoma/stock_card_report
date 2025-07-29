# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th) License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import statistics

from odoo import api, fields, models, _

from odoo.exceptions import UserError


class StockCardView(models.TransientModel):
    _name = 'stock.card.view'
    _description = 'Stock Card View'
    _order = 'date'

    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name='product.product')
    move_id = fields.Many2one(comodel_name='stock.move')
    product_uom = fields.Many2one(comodel_name='uom.uom')
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name='stock.location')
    location_dest_id = fields.Many2one(comodel_name='stock.location')
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    value = fields.Float()
    price_unit = fields.Float()
    landed_cost_value = fields.Float()
    origin = fields.Char()
    lot_id = fields.Many2one(comodel_name="stock.production.lot")
    partner_id = fields.Many2one(comodel_name="res.partner")


class StockCardReport(models.TransientModel):
    _name = 'report.stock.card.report'
    _description = 'Stock Card Report'

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(
        comodel_name='product.product',
    )
    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse',)
    location_ids = fields.Many2many(
        comodel_name='stock.location',
    )
    # All locations included in the report, requested by the user
    # or computed in the generation process.
    reported_location_ids = fields.Many2many(
        comodel_name='stock.location',
    )
    categ_ids = fields.Many2many(
        comodel_name='product.category',
        string='Products Category',
    )
    lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string='Product Lots',
    )
    consolidated = fields.Boolean(string='Consolidated Report?')

    group_by_lot = fields.Boolean(string='Group by lot')
    group_by_location = fields.Boolean(string='Group by location')
    show_lot = fields.Boolean(string='Show Lot')
    show_partner = fields.Boolean(string='Show Partner')
    include_sublocations = fields.Boolean(string='Include sublocations')
    only_accounted_moves = fields.Boolean(string='Only Accounted Moves')
    code_from = fields.Char()
    code_to = fields.Char()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='stock.card.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )
    sku_type = fields.Selection([
            ('code','Codigo'),
            ('barcode','Barcode'),
        ], default="code",
        string='SKU type',
    )

    def _filter_warehouse_ids(self, locations):
        if self.warehouse_ids:
            locations = locations.filtered(lambda l: l.get_warehouse().id in self.warehouse_ids.ids)
        return locations

    @api.multi
    def _compute_results(self):
        # Hack to avoid computing several reports on update.
        if len(self) != 1:
            return
        products = self.env['product.product']
        if not self.location_ids:
            locations = self.env['stock.location'].search(
                [('usage', 'in', ('internal', 'transit'))]
            )
            if self.warehouse_ids:
                locations = self._filter_warehouse_ids(locations)
        else:
            locations = self.location_ids
        if self.include_sublocations:
            locations = self.env['stock.location'].search(
               [('id', 'child_of', locations.ids)])
        # We will use reported_location_ids later to filter the
        # required locations in the final report.
        self.reported_location_ids = locations
        if self.product_ids:
            products += self.env['product.product'].search(
                [('id', 'in', self.product_ids.ids)])
        if self.categ_ids:
            categories = self.env['product.category'].search(
                [('id', 'child_of', self.categ_ids.ids)])
            products += self.env['product.product'].search(
                [('categ_id', 'in', categories.ids)])
        if self.code_from or self.code_to:
            code_from = self.code_from or "0"
            code_to = self.code_to or "Z"
            code_list = list("0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ")
            code_range = code_list[code_list.index(code_from):code_list.index(code_to)+1]
            field_code = 'default_code'
            if self.sku_type == 'barcode':
                field_code = 'barcode'
            for cr in code_range:
                products += self.env['product.product'].search(
                    [(field_code, '=ilike', cr+'%')]
                )
        self.product_ids = products

        params = []

        query = """
           SELECT move.id AS move_id, move.date, move.product_id,
                move.product_uom, move.reference,
                move.price_unit,\n"""

        if self.show_lot:
            query += "line.lot_id,\n"

        if self.show_partner:
            query += "picking.partner_id,\n"

        if not self.show_lot and not self.lot_ids and self.include_sublocations:
            query += """
                move.value, move.landed_cost_value,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in {0}
                    then move.product_uom_qty end as product_in,
                case when move.location_id in {0}
                    then move.product_uom_qty end as product_out,\n"""
        else:
            query += """
                move.value * (line.qty_done/move.product_uom_qty) AS value,
                move.landed_cost_value * (line.qty_done/move.product_uom_qty) AS landed_cost_value,
                line.location_id, line.location_dest_id,
                case when line.location_dest_id in {0}
                    then line.qty_done end as product_in,
                case when line.location_id in {0}
                    then line.qty_done end as product_out,\n"""

        query += """

            case when move.date < '{3}' then True else False end as is_initial,
                picking.origin
            FROM stock_move AS move
            LEFT JOIN stock_picking picking ON picking.id = move.picking_id
            """

        if self.only_accounted_moves:
            query += """LEFT JOIN account_move as account ON move.id = account.stock_move_id\n"""

        if not self.show_lot and not self.lot_ids and self.include_sublocations:
            # No need to join as all information is on the move.
            # Done this way to keep the logic of previus if.
            pass
        else:
            query += """INNER JOIN stock_move_line as line ON line.move_id = move.id\n"""

        if self.include_sublocations:
            query += """WHERE (move.location_id in {0} or move.location_dest_id in {0})\n"""
        else:
            query += """WHERE (line.location_id in {0} or line.location_dest_id in {0})\n"""

        query += """
            and move.state = 'done' and move.product_id in {1}
            and CAST(move.date AS date) <= '{2}'\n"""

        if self.only_accounted_moves:
            query += "    and account.stock_move_id IS NOT NULL\n"

        if self.lot_ids:
            query += "    and line.lot_id in {4}\n"

        query += """
            ORDER BY move.date, move.reference
            """

        query = query.format(
            tuple(locations.ids+[0]), #{0}
            tuple(self.product_ids.ids+[0]), #{1}
            self.date_to, #{2}
            self.date_from, #{3}
            tuple(self.lot_ids.ids+[0]) #{4}
        )

        self._cr.execute(query, params)
        stock_card_results = self._cr.dictfetchall()
        ReportLine = self.env['stock.card.view']
        for line in stock_card_results:
            self.results += ReportLine.new(line)

    @api.multi
    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped('product_in'))
        product_output_qty = sum(product_line.mapped('product_out'))
        return product_input_qty - product_output_qty

    @api.multi
    def _get_initial_value(self, product_line):
        value = 0
        for line in product_line:
            line_product_in = line.product_in or 0
            line_product_out = line.product_out or 0
            net_qty = (line_product_in - line_product_out)
            abs_line_value = abs(line.value)
            if net_qty > 0:
                value += abs_line_value
            elif net_qty < 0:
                value += -abs_line_value

        return value

    @api.multi
    def _get_initial_inventory_value(self, product_line):
        net_value = 0
        for line in product_line:
            line_product_in = line.product_in or 0
            line_product_out = line.product_out or 0
            net_qty = (line_product_in - line_product_out)
            abs_value = abs(line.value + line.landed_cost_value)
            if net_qty > 0:
                net_value += abs_value
            elif net_qty < 0:
                net_value += -abs_value

        return net_value

    @api.multi
    def _get_initial_landed_cost_value(self, product_line):
        product_input_value = sum(product_line.filtered(lambda x: x.product_in > 0).mapped('landed_cost_value'))
        product_output_value = sum(product_line.filtered(lambda x: x.product_out > 0).mapped('landed_cost_value'))
        return product_input_value - product_output_value

    @api.multi
    def _get_initial_landed_cost_value(self, product_line):
        product_input_value = sum(product_line.filtered(lambda x: x.product_in > 0).mapped('landed_cost_value'))
        product_output_value = sum(product_line.filtered(lambda x: x.product_out > 0).mapped('landed_cost_value'))
        return product_input_value - product_output_value

    @api.multi
    def _get_initial_price_unit(self, product_line):
        if not product_line:
            return 0.000
        return statistics.mean(product_line.mapped('price_unit'))

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref(
            'stock_card_report.action_stock_card_report_xlsx') or \
            self.env.ref('stock_card_report.action_stock_card_report_pdf')
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'stock_card_report.report_stock_card_report_html').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

