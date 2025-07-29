# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th) License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import statistics
import json

from odoo import api, fields, models, _

from odoo.exceptions import UserError


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
    results = fields.Binary(
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
        # The general query structure is similar for all cases, what changes
        # is the source of the data (stock.move or stock.move.line) and the
        # conditions.
        query_template = """
            SELECT move.id AS move_id, move.date, move.product_id,
                move.product_uom, move.reference,
                move.price_unit,
                {lot_select}
                {partner_select}
                {value_select}
                {landed_cost_select}
                {location_select}
                {location_dest_select}
                CASE WHEN {location_dest_field} in %s
                    THEN {qty_field} END as product_in,
                CASE WHEN {location_field} in %s
                    THEN {qty_field} END as product_out,
                CASE WHEN move.date < %s THEN True ELSE False END as is_initial,
                picking.origin
            FROM stock_move AS move
            LEFT JOIN stock_picking picking ON picking.id = move.picking_id
            {move_line_join}
            {account_join}
            WHERE ({location_filter})
            AND move.state = 'done' AND move.product_id in %s
            AND CAST(move.date AS date) <= %s
            {account_where}
            {lot_where}
            ORDER BY move.date, move.reference
        """

        # We build the query based on the report options
        lot_select = "line.lot_id," if self.show_lot else ""
        partner_select = "picking.partner_id," if self.show_partner else ""
        account_join = ""
        account_where = ""
        if self.only_accounted_moves:
            account_join = "LEFT JOIN account_move as account ON move.id = account.stock_move_id"
            account_where = "AND account.stock_move_id IS NOT NULL"

        lot_where = ""
        if self.lot_ids:
            lot_where = "AND line.lot_id in %s"
        else:
            # We need to remove the %s from the query if there are no lots
            query_template = query_template.replace("{lot_where}", "")

        # If we are not showing lots, we can use the stock_move table directly
        if not self.show_lot and not self.lot_ids and self.include_sublocations:
            move_line_join = ""
            location_field = "move.location_id"
            location_dest_field = "move.location_dest_id"
            qty_field = "move.product_uom_qty"
            value_select = "move.value,"
            landed_cost_select = "move.landed_cost_value,"
            location_select = "move.location_id,"
            location_dest_select = "move.location_dest_id,"
            location_filter = "move.location_id in %s OR move.location_dest_id in %s"
        else:
            move_line_join = "INNER JOIN stock_move_line as line ON line.move_id = move.id"
            location_field = "line.location_id"
            location_dest_field = "line.location_dest_id"
            qty_field = "line.qty_done"
            value_select = "move.value * (line.qty_done/move.product_uom_qty) AS value,"
            landed_cost_select = "move.landed_cost_value * (line.qty_done/move.product_uom_qty) AS landed_cost_value,"
            location_select = "line.location_id,"
            location_dest_select = "line.location_dest_id,"
            location_filter = "line.location_id in %s OR line.location_dest_id in %s"

        query = query_template.format(
            lot_select=lot_select,
            partner_select=partner_select,
            value_select=value_select,
            landed_cost_select=landed_cost_select,
            location_select=location_select,
            location_dest_select=location_dest_select,
            location_dest_field=location_dest_field,
            location_field=location_field,
            qty_field=qty_field,
            move_line_join=move_line_join,
            account_join=account_join,
            location_filter=location_filter,
            account_where=account_where,
            lot_where=lot_where,
        )

        params = [
            tuple(locations.ids + [0]),
            tuple(locations.ids + [0]),
            self.date_from,
            tuple(locations.ids + [0]),
            tuple(locations.ids + [0]),
            tuple(self.product_ids.ids + [0]),
            self.date_to,
        ]
        params.insert(3, tuple(locations.ids + [0]))
        params.insert(4, tuple(locations.ids + [0]))
        if self.lot_ids:
            params.append(tuple(self.lot_ids.ids + [0]))



        self._cr.execute(query, tuple(params))
        stock_card_results = self._cr.dictfetchall()
        self.results = json.dumps(stock_card_results, default=str).encode('utf-8')

    @api.multi
    def _get_initial(self, product_line):
        product_input_qty = sum([l['product_in'] or 0 for l in product_line])
        product_output_qty = sum([l['product_out'] or 0 for l in product_line])
        return product_input_qty - product_output_qty

    @api.multi
    def _get_initial_value(self, product_line):
        value = 0
        for line in product_line:
            line_product_in = line['product_in'] or 0
            line_product_out = line['product_out'] or 0
            net_qty = (line_product_in - line_product_out)
            abs_line_value = abs(line['value'])
            if net_qty > 0:
                value += abs_line_value
            elif net_qty < 0:
                value += -abs_line_value

        return value

    @api.multi
    def _get_initial_inventory_value(self, product_line):
        net_value = 0
        for line in product_line:
            line_product_in = line['product_in'] or 0
            line_product_out = line['product_out'] or 0
            net_qty = (line_product_in - line_product_out)
            abs_value = abs(line['value'] + line['landed_cost_value'])
            if net_qty > 0:
                net_value += abs_value
            elif net_qty < 0:
                net_value += -abs_value

        return net_value

    @api.multi
    def _get_initial_landed_cost_value(self, product_line):
        product_input_value = sum([l['landed_cost_value'] for l in product_line if l['product_in'] > 0])
        product_output_value = sum([l['landed_cost_value'] for l in product_line if l['product_out'] > 0])
        return product_input_value - product_output_value

    @api.multi
    def _get_initial_price_unit(self, product_line):
        if not product_line:
            return 0.000
        return statistics.mean([l['price_unit'] for l in product_line])

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

