# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.onchange('country_id')
    def onchange_country(self):
        """ Ecuadorian companies use round_globally as tax_calculation_rounding_method """
        for rec in self.filtered(lambda x: x.country_id == self.env.ref('base.ec')):
            rec.tax_calculation_rounding_method = 'round_globally'

    def _localization_use_documents(self):
        """ Ecuadorian localization use documents """
        self.ensure_one()
        return True if self.country_id == self.env.ref('base.ec') else super()._localization_use_documents()

    l10n_ec_consumidor_final_limit = fields.Float(string="Invoice Sales Limit Final Consumer", default=200.0)

    l10n_ec_withhold_sale_iva_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Withhold Sales IVA Account',
        required=False)

    l10n_ec_withhold_sale_iva_tag_id = fields.Many2one(
        comodel_name='account.account.tag',
        string='Withhold Sales IVA Account Tag',
        required=False)

    l10n_ec_withhold_sale_rent_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Withhold Sales Rent Account',
        required=False)

    l10n_ec_withhold_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Withhold Journal',
        required=False)
