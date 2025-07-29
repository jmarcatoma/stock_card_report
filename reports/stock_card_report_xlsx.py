# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
import json
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class ReportStockCardReportXlsx(models.TransientModel):
    _name = 'report.stock_card_report.report_stock_card_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        data = json.loads(objects.results)
        for ws_params in self._get_ws_params(workbook, data, objects):
            ws_name = ws_params.get('ws_name')
            ws_name = self._check_ws_name(ws_name)
            ws = workbook.add_worksheet(ws_name)
            generate_ws_method = getattr(
                self, ws_params['generate_ws_method'])
            generate_ws_method(
                workbook, ws, ws_params, data, objects)

    def _get_ws_params(self, wb, data, objects):
        code_header = _('Default Code')
        if objects.sku_type == 'barcode':
            code_header = _('Código de barras')
        stock_card_template = {
            '10_code': {
                'header': {
                    'value': code_header,
                },
                'data': {
                    'value': self._render('code'),
                },
                'width': 25,
            },
            '11_product': {
                'header': {
                    'value': _('Product'),
                },
                'data': {
                    'value': self._render('product_id'),
                },
                'width': 25,
            },
        }
        if objects.consolidated:
            stock_card_template.update({
                '20_init_value': {
                    'header': {
                        'value': _('Valoración inicial'),
                    },
                    'data': {
                        'value': self._render('init_value'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '22_init_landed_cost_value': {
                    'header': {
                        'value': _('Costos en destino iniciales'),
                    },
                    'data': {
                        'value': self._render('init_landed_cost_value'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '24_init_total_value': {
                    'header': {
                        'value': _('Valor total del inventario inicial'),
                    },
                    'data': {
                        'value': self._render('init_total_value'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '26_init_avg_price_unit': {
                    'header': {
                        'value': _('Valor unitario promedio inicial'),
                    },
                    'data': {
                        'value': self._render('init_avg_price_unit'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '30_balance': {
                    'header': {
                        'value': _('Inventario inicial'),
                    },
                    'data': {
                        'value': self._render('balance'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '32_product_in': {
                    'header': {
                        'value': _('Entradas'),
                    },
                    'data': {
                        'value': self._render('product_in'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '34_product_out': {
                    'header': {
                        'value': _('Salidas'),
                    },
                    'data': {
                        'value': self._render('product_out'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
                '40_end_balance': {
                    'header': {
                        'value': _('Inventario final'),
                    },
                    'data': {
                        'value': self._render('end_balance'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
            })
            if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
                stock_card_template.update({
                    '42_value': {
                        'header': {
                            'value': _('Valoración final'),
                        },
                        'data': {
                            'value': self._render('value'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                    '44_landed_cost_value': {
                        'header': {
                            'value': _('Costos en destino finales'),
                        },
                        'data': {
                            'value': self._render('landed_cost_value'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                    '46_total_value': {
                        'header': {
                            'value': _('Valoración total final'),
                        },
                        'data': {
                            'value': self._render('total_value'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                    '48_avg_price_unit': {
                        'header': {
                            'value': _('Valor unitario final'),
                        },
                        'data': {
                            'value': self._render('avg_price_unit'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                })
        if not objects.consolidated:
            stock_card_template.update({
                '20_date': {
                    'header': {
                        'value': _('Date'),
                    },
                    'data': {
                        'value': self._render('date'),
                        'type': 'datetime',
                        'format': self.format_tcell_date_left,
                    },
                    'width': 25,
                },
                '22_loc_src': {
                    'header': {
                        'value': _('Source location'),
                    },
                    'data': {
                        'value': self._render('location_id'),
                    },
                    'width': 25,
                },
                '24_loc_dest': {
                    'header': {
                        'value': _('Destination location'),
                    },
                    'data': {
                        'value': self._render('location_dest_id'),
                    },
                    'width': 25,
                },
                '40_reference': {
                    'header': {
                        'value': _('Reference'),
                    },
                    'data': {
                        'value': self._render('reference'),
                    },
                    'width': 25,
                },
                '45_origin': {
                    'header': {
                        'value': _('Origen'),
                    },
                    'data': {
                        'value': self._render('origin'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 25,
                },
            })
            if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
                stock_card_template.update({
                    '50_price_unit': {
                        'header': {
                            'value': _('Price Unit'),
                        },
                        'data': {
                            'value': self._render('price_unit'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                    '60_value': {
                        'header': {
                            'value': _('Value'),
                        },
                        'data': {
                            'value': self._render('value'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                    '70_landed_cost': {
                        'header': {
                            'value': _('Landed cost value'),
                        },
                        'data': {
                            'value': self._render('landed_cost_value'),
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 25,
                    },
                })
            stock_card_template.update({
                '80_input': {
                    'header': {
                        'value': _('Input'),
                    },
                    'data': {
                        'value': self._render('input'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 20,
                },
                '85_output': {
                    'header': {
                        'value': _('Output'),
                    },
                    'data': {
                        'value': self._render('output'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 20,
                },
                '90_balance_qty': {
                    'header': {
                        'value': _('Balance (qty)'),
                    },
                    'data': {
                        'value': self._render('balance'),
                        'format': self.format_tcell_amount_right,
                    },
                    'width': 20,
                },
            })
            if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
                stock_card_template.update({
                    '91_inventory_value': {
                        'header': {
                            'value': _('Inventory value'),
                        },
                        'data': {
                            'value': self._render('inventory_value') ,
                            'format': self.format_tcell_amount_right,
                        },
                        'width': 20,
                    },
                })
            if self.env.user.has_group("account.group_account_user"):
                stock_card_template.update({
                    '99_account_move': {
                        'header': {
                            'value': _('Account Move'),
                        },
                        'data': {
                            'value': self._render('account_move_ids'),
                        },
                        'width': 25,
                    },
                })
            if objects.show_lot:
                stock_card_template.update({
                    '20_init_value': {
                        'header': {
                            'value': _('Lot'),
                        },
                        'data': {
                            'value': self._render('lot_id'),
                        },
                        'width': 25,
                    }
                })
            if objects.show_partner:
                stock_card_template.update({
                    '18_init_value': {
                        'header': {
                            'value': _('Partner'),
                        },
                        'data': {
                            'value': self._render('partner_id'),
                        },
                        'width': 45,
                    }
                })

        ws_params = {
            'ws_name': "STOCK CARD REPORT",
            'generate_ws_method': '_stock_card_report',
            'title': 'STOCK CARD REPORT',
            'wanted_list': [k for k in sorted(stock_card_template.keys())],
            'col_specs': stock_card_template,
        }
        return [ws_params]

    def _stock_card_report(self, wb, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)

        for o in objects:
            ws.write_row(
                row_pos, 0, [_('Date from'), _('Date to'), _('Locations'), _('Warehouses')],
                self.format_theader_blue_center)
            ws.write_row(row_pos+1, 0, [o.date_from or '', o.date_to or ''],
                         self.format_tcell_date_center)
            # Show name of selected locations and warehouses, if none is selected,
            # it's empty to avoid printing all warehouses and locations..
            ws.write_row(row_pos+1, 2, [
                ", ".join(o.location_ids.mapped('display_name')),
                ", ".join(o.warehouse_ids.mapped('display_name'))
                ], self.format_tcell_center)

            row_pos += 3
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='header',
                default_format=self.format_theader_blue_center)
            ws.freeze_panes(row_pos, 0)

            product_ids = list(set([l['product_id'] for l in data]))
            products = self.env['product.product'].browse(product_ids)

            location_ids = list(set([l['location_id'] for l in data] + [l['location_dest_id'] for l in data]))
            locations = self.env['stock.location'].browse(location_ids)
            location_names = {loc.id: loc.display_name for loc in locations}

            lot_ids = list(set([l.get('lot_id') for l in data if l.get('lot_id')]))
            lots = self.env['stock.production.lot'].browse(lot_ids)
            lot_names = {lot.id: lot.name for lot in lots}

            partner_ids = list(set([l.get('partner_id') for l in data if l.get('partner_id')]))
            partners = self.env['res.partner'].browse(partner_ids)
            partner_names = {partner.id: partner.name for partner in partners}

            for product in products:
                p_lines = [l for l in data if l['product_id'] == product.id]
                # We compute the location in the lines to avoid printing a section if there is no
                # product lines on a selected warehouse or location and to include computed locations,
                # for example, when only warehouse is provided and we print all it's locations.
                product_locations = list(set([l['location_dest_id'] for l in p_lines] + [l['location_id'] for l in p_lines]))
                product_locations = self.env['stock.location'].browse(product_locations)
                product_locations = product_locations.filtered(lambda x: x in o.reported_location_ids)

                if not o.group_by_lot and not o.group_by_location:
                    row_pos = self._render_report_lines(
                        o, ws, row_pos, ws_params, p_lines, product, loc_ids=product_locations,
                        location_names=location_names, lot_names=lot_names, partner_names=partner_names
                    )

                elif o.group_by_lot and not o.group_by_location:
                    lot_ids = list(set([l['lot_id'] for l in p_lines if l['lot_id']]))
                    lots = self.env['stock.production.lot'].browse(lot_ids)
                    for lot in lots:
                        lot_lines = [l for l in p_lines if l['lot_id'] == lot.id]
                        row_pos = self._render_report_lines(
                            o, ws, row_pos, ws_params, lot_lines, product, lot_id=lot,
                            loc_ids=product_locations,
                            include_sublocations=o.include_sublocations,
                            location_names=location_names, lot_names=lot_names, partner_names=partner_names)
                elif o.group_by_location:
                    # We exclude all sublocations if the report is marked to include sublocations, to
                    # avoid printing the same location recursive as a child and on it's own sections.
                    if o.include_sublocations:
                        product_locations -= product_locations.filtered(lambda x: x.location_id in product_locations)
                    for loc in product_locations:
                        if o.consolidated:
                            ws.write_row(row_pos, 0, ['', '','','',''],
                                self.format_tcell_center,)
                            row_pos += 1
                            # Write a title line to find different scenarios easily.
                            ws.write_row(row_pos, 0, [
                                loc.display_name or '',
                                o.include_sublocations and _("INCLUDE SUBLOCATIONS") or ''],
                                self.format_theader_blue_center, )
                            row_pos += 1
                        if o.include_sublocations:
                            loc_ids = self.env["stock.location"].search([("id", "child_of", loc.id)])
                        else:
                            loc_ids = loc
                        loc_lines = [l for l in p_lines if l['location_id'] in loc_ids.ids or l['location_dest_id'] in loc_ids.ids]
                        if not o.group_by_lot:
                            row_pos = self._render_report_lines(
                                o, ws, row_pos, ws_params, loc_lines, product, location_id=loc,
                                loc_ids=loc_ids, include_sublocations=o.include_sublocations,
                                location_names=location_names, lot_names=lot_names, partner_names=partner_names)
                        else:
                            lot_ids = list(set([l['lot_id'] for l in loc_lines if l['lot_id']]))
                            lots = self.env['stock.production.lot'].browse(lot_ids)
                            for lot in lots:
                                lot_lines_per_lot = [l for l in loc_lines if l['lot_id'] == lot.id]
                                row_pos = self._render_report_lines(
                                    o, ws, row_pos, ws_params, lot_lines_per_lot, product,
                                    lot_id=lot, location_id=loc, loc_ids=loc_ids,
                                    include_sublocations=o.include_sublocations,
                                    location_names=location_names, lot_names=lot_names, partner_names=partner_names
                                )

    def _render_report_lines(
            self, o, ws, row_pos, ws_params, lines, product,
            lot_id=False, location_id=False, loc_ids=False,
            include_sublocations=False, location_names=None,
            lot_names=None, partner_names=None):
        if not lines:
            return row_pos
        if o.consolidated:
            return self._render_consolidated_lines(
                o, ws, row_pos, ws_params, lines, product,
                lot_id, location_id, loc_ids,
                location_names=location_names, lot_names=lot_names,
                partner_names=partner_names)
        else:
            return self._render_detailed_lines(
                o, ws, row_pos, ws_params, lines, product,
                lot_id, location_id, loc_ids, include_sublocations,
                location_names=location_names, lot_names=lot_names,
                partner_names=partner_names)

    def _render_consolidated_lines(
            self, o, ws, row_pos, ws_params, lines, product,
            lot_id=False, location_id=False, loc_ids=False,
            location_names=None, lot_names=None, partner_names=None):
        product_lines = [l for l in lines if not l['is_initial']]
        initial_lines = [l for l in lines if l['is_initial']]
        balance = o._get_initial(initial_lines)

        if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
            init_landed_cost_value = o._get_initial_landed_cost_value(initial_lines)
            init_avg_price_unit = o._get_initial_price_unit([l for l in initial_lines if (l.get('price_unit') or 0) > 0])
            init_value = o._get_initial_value(initial_lines)
        else:
            init_landed_cost_value = 0
            init_avg_price_unit = 0
            init_value = 0

        code = product.default_code or ''
        if o.sku_type == 'barcode':
            code = product.barcode or ''

        # Init values
        init_total_value = init_value + init_landed_cost_value

        # Init values.
        product_in = 0
        product_out = 0
        line_value = 0

        if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
            for line in product_lines:
                line_product_in = line['product_in'] if line['location_dest_id'] in loc_ids.ids else 0
                line_product_out = line['product_out'] if line['location_id'] in loc_ids.ids else 0
                net_qty = (line_product_in - line_product_out)
                abs_line_value = abs(line['value'] or 0)
                if net_qty > 0:
                    line_value += abs_line_value
                elif net_qty < 0:
                    line_value += -abs_line_value

                product_in += line_product_in
                product_out += line_product_out

            end_balance = balance + product_in - product_out
            value = line_value
            landed_cost_value = sum([l['landed_cost_value'] for l in product_lines])
            total_value = value + landed_cost_value + init_value + init_landed_cost_value
            avg_price_unit = 0 if end_balance == 0 else total_value/end_balance
        else:
            value = 0
            landed_cost_value = 0
            total_value = 0
            avg_price_unit = 0

        render_space={
            'product_id': product and product.display_name or '',
            'code': code,
            'init_value': init_value or 0,
            'init_landed_cost_value': init_landed_cost_value or 0,
            'init_total_value': init_total_value,
            'init_avg_price_unit': init_avg_price_unit,
            'balance': balance,
            'product_in': product_in,
            'product_out': product_out,
            'end_balance': end_balance,
            'value': init_value + value,
            'landed_cost_value': landed_cost_value + init_landed_cost_value,
            'total_value': total_value,
            'avg_price_unit': avg_price_unit,
            'lot_id': lot_id and lot_id.name or "",
            'location_id': location_id and location_id.display_name or "",
        }
        return self._write_line(
            ws, row_pos, ws_params, col_specs_section='data',
            render_space=render_space,
            default_format=self.format_tcell_left)

    def _render_detailed_lines(
            self, o, ws, row_pos, ws_params, lines, product,
            lot_id=False, location_id=False, loc_ids=False,
            include_sublocations=False, location_names=None,
            lot_names=None, partner_names=None):
        product_lines = [l for l in lines if not l['is_initial']]
        initial_lines = [l for l in lines if l['is_initial']]
        balance = o._get_initial(initial_lines)

        if self.env.user.has_group("abs_hide_sale_cost_price.group_cost_price_show"):
            init_landed_cost_value = o._get_initial_landed_cost_value(initial_lines)
            init_avg_price_unit = o._get_initial_price_unit([l for l in initial_lines if (l['price_unit'] or 0) > 0])
            init_value = o._get_initial_value(initial_lines)
            init_inventory_value = o._get_initial_inventory_value(initial_lines)
        else:
            init_landed_cost_value = 0
            init_avg_price_unit = 0
            init_value = 0
            init_inventory_value = 0

        code = product.default_code or ''
        if o.sku_type == 'barcode':
            code = product.barcode or ''

        inventory_value = 0
        # We add a blank line in consolidated report to have a division between segments.
        ws.write_row(row_pos, 0, ['', '', '', '', ''],
                     self.format_tcell_center, )
        row_pos += 1
        # Write a title line to find different scenarios easily.
        ws.write_row(row_pos, 0, [
            code,
            product.display_name,
            lot_id and lot_id.name or '',
            location_id and location_id.display_name or '',
            include_sublocations and _("INCLUDE SUBLOCATIONS") or ''],
                     self.format_theader_blue_center, )
        row_pos += 1
        render_space = {
            'product_id': product.display_name or '',
            'code': code,
            'reference': _("INIT BALANCE"),
            'balance': balance,
            'value': init_value,
            'landed_cost_value': init_landed_cost_value,
            'price_unit': init_avg_price_unit,
            'date': o.date_from,
            'origin': '',
            'account_move_ids': '',
            'input': '',
            'output': '',
            'inventory_value': init_inventory_value,
            'location_id': '',
            'location_dest_id': '',
        }
        if o.show_partner:
            render_space.update({"partner_id": ""})
        if o.show_lot:
            render_space.update({"lot_id": lot_id and lot_id.name or ""})
        row_pos = self._write_line(
            ws, row_pos, ws_params, col_specs_section='data',
            render_space=render_space,
            default_format=self.format_tcell_left
        )
        inventory_value += init_inventory_value

        for line in product_lines:
            account_moves = ''
            net_value = 0
            line_value = 0
            line_price_unit = 0
            if self.env.user.has_group("account.group_account_user"):
                move_id = self.env['stock.move'].browse(line['move_id'])
                posted_moves = move_id.account_move_ids.filtered(lambda x: x.state == 'posted')
                if posted_moves:
                    account_moves += ", ".join([
                        l.name + ' (' + "{0:.2f}".format(round(l.amount, 2)) + ')' \
                        for l in posted_moves
                    ])
                if line['landed_cost_value']:
                    # Search for the account moves related to the landed costs
                    landed_cost_ids = self.env['stock.landed.cost'].search([
                        ('state', '=', 'done'),
                        ('picking_ids', 'in', move_id.picking_id.id)
                    ])
                    for cost in landed_cost_ids:
                        for move in cost.account_move_id.line_ids.filtered(
                                lambda r: r.product_id.id == line['product_id'] and r.debit > 0):
                            account_moves += (
                                (account_moves and ', ' or '') +
                                f"{cost.account_move_id.name} ({move.debit:.2f})"
                            )

            product_in = line['product_in'] if line['location_dest_id'] in loc_ids.ids else 0
            product_out = line['product_out'] if line['location_id'] in loc_ids.ids else 0
            net_qty = (product_in - product_out)
            balance += net_qty
            abs_value = abs((line['value'] or 0) + (line['landed_cost_value'] or 0))
            abs_line_value = abs(line['value'] or 0)
            abs_line_price_unit = abs(line['price_unit'] or 0)
            if net_qty > 0:
                net_value = abs_value
                line_value = abs_line_value
                line_price_unit = abs_line_price_unit
            elif net_qty < 0:
                net_value = -abs_value
                line_value = -abs_line_value
                line_price_unit = -abs_line_price_unit
            inventory_value += net_value
            report_values = {
                    'date': line['date'] and datetime.strptime(line['date'], '%Y-%m-%d %H:%M:%S') or '',
                'product_id': product.display_name or '',
                'code': code,
                'reference': line['reference'] or '',
                'origin': line['origin'] or '',
                'price_unit': line_price_unit or 0.000,
                'account_move_ids': account_moves,
                'input': product_in,
                'output': product_out,
                'balance': balance,
                'value': line_value or 0.000,
                'inventory_value': inventory_value or 0.000,
                'landed_cost_value': line['landed_cost_value'],
                'location_id': location_names.get(line['location_id'], ''),
                'location_dest_id': location_names.get(line['location_dest_id'], '')
            }
            if o.show_partner:
                report_values.update({"partner_id": partner_names.get(line['partner_id'], '')})
            if o.show_lot:
                report_values.update({"lot_id": lot_names.get(line['lot_id'], '')})
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='data',
                render_space=report_values,
                default_format=self.format_tcell_left
            )
        return row_pos
