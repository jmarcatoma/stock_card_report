from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockCardSelectCategoryWizard(models.TransientModel):
    _name = 'stock.card.select.category.wizard'
    _description = 'Select Categories Wizard'

    wizard_id = fields.Many2one('stock.card.report.wizard', required=True)
    category_ids = fields.Many2many('product.category', string='Select Categories')

    @api.multi
    def apply_selected_categories(self):
        self.ensure_one()
        if self.wizard_id:
            self.wizard_id.categ_ids = [(6, 0, self.category_ids.ids)]

            return {
                'name': 'Stock Card Report',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.card.report.wizard',
                'view_mode': 'form',
                'res_id': self.wizard_id.id,
                'target': 'new',
            }
