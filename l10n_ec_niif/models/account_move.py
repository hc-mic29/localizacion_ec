# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class L10nECIdentificationType(models.Model):

    _name = 'l10n_ec.identification.type'

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
    document_type_ids = fields.Many2many('l10n_latam.document.type', string='Tipos de Transacciones Asociadas')
    default_invoice_document_type_id = fields.Many2one(comodel_name="l10n_latam.document.type",
                                                       string="Default Document Type for Invoices", required=False, )
    default_credit_note_document_type_id = fields.Many2one(comodel_name="l10n_latam.document.type",
                                                           string="Default Document Type for Credit Notes",
                                                           required=False, )
    default_debit_note_document_type_id = fields.Many2one(comodel_name="l10n_latam.document.type",
                                                          string="Default Document Type for Debit Notes",
                                                          required=False, )

    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        recs = self.browse()
        res = super(L10nECIdentificationType, self)._name_search(name, args, operator, limit, name_get_uid)
        if not res and name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
            if not recs:
                recs = self.search([('code', operator, name)] + args, limit=limit)
            if recs:
                res = models.lazy_name_get(self.browse(recs.ids).with_user(name_get_uid)) or []
        return res

    def name_get(self):
        res = []
        for r in self:
            name = "%s - %s" % (r.code, r.name)
            res.append((r.id, name))
        return res

class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ec_tax_support_id = fields.Many2one(comodel_name="l10n_ec.tax.support",
                                             string="Tax Support", required=False, )
    l10n_ec_is_exportation = fields.Boolean(string="Is Exportation?")
    l10n_ec_tipo_regimen_pago_exterior = fields.Selection([
        ('01', 'Régimen general'),
        ('02', 'Paraíso fiscal'),
        ('03', 'Régimen fiscal preferente o jurisdicción de menor imposición')
        ], string='Tipo de regimen fiscal del exterior',
         states={}, help=u"")
    l10n_ec_aplica_convenio_doble_tributacion = fields.Selection([
        ('si', 'SI'),
        ('no','NO'),
        ], string='Aplica convenio doble tributación',
         states={}, help=u"")
    l10n_ec_pago_exterior_sujeto_retencion = fields.Selection([
        ('si', 'SI'),
        ('no','NO'),
        ], string='Pago sujeto a retención',
         states={}, help=u"")
    l10_ec_foreign = fields.Boolean(u'Foreign?',
                                    related='partner_id.l10_ec_foreign', store=True)

    @api.depends(
        'partner_id.l10_ec_type_sri',
        'l10n_ec_is_exportation',
        'type',
        'company_id',
    )
    def _get_l10n_ec_identification_type(self):
        def get_identification(code):
            identification_model = self.env['l10n_ec.identification.type']
            identification = identification_model.search([
                ('code', '=', code)
            ])
            return identification and identification.id or False
        for move in self:
            if move.company_id.country_id.code == 'EC':
                domain = []
                if move.partner_id.l10_ec_type_sri:
                    if move.type in ('in_invoice', 'in_refund'):
                        if move.partner_id.l10_ec_type_sri == 'Ruc':
                            move.l10n_ec_identification_type_id = get_identification('01')
                        elif move.partner_id.l10_ec_type_sri == 'Cedula':
                            move.l10n_ec_identification_type_id = get_identification('02')
                        elif move.partner_id.l10_ec_type_sri == 'Pasaporte':
                            move.l10n_ec_identification_type_id = get_identification('03')
                        else:
                            move.l10n_ec_identification_type_id = False
                    elif move.type in ('out_invoice', 'out_refund'):
                        if not move.l10n_ec_is_exportation:
                            if move.partner_id.l10_ec_type_sri == 'Ruc':
                                move.l10n_ec_identification_type_id = get_identification('04')
                            elif move.partner_id.l10_ec_type_sri == 'Cedula':
                                move.l10n_ec_identification_type_id = get_identification('05')
                            elif move.partner_id.l10_ec_type_sri == 'Pasaporte':
                                move.l10n_ec_identification_type_id = get_identification('06')
                            elif move.partner_id.l10_ec_type_sri == 'Consumidor':
                                move.l10n_ec_identification_type_id = get_identification('07')
                            else:
                                move.l10n_ec_identification_type_id = False
                        else:
                            if move.partner_id.l10_ec_type_sri == 'Ruc':
                                move.l10n_ec_identification_type_id = get_identification('20')
                            elif move.partner_id.l10_ec_type_sri == 'Pasaporte':
                                move.l10n_ec_identification_type_id = get_identification('21')
                            else:
                                move.l10n_ec_identification_type_id = False
                else:
                    move.l10n_ec_identification_type_id = False
                if move.l10n_ec_identification_type_id:
                    move.l10n_ec_document_type_domain_ids = move.l10n_ec_identification_type_id.document_type_ids.ids
                    if move.l10n_ec_document_type_domain_ids and \
                            move.l10n_latam_document_type_id.id not in move.l10n_ec_document_type_domain_ids.ids:
                        move.l10n_latam_document_type_id = move.l10n_ec_document_type_domain_ids.ids[0]

    l10n_ec_identification_type_id = fields.Many2one('l10n_ec.identification.type',
                                                     string="Ecuadorian Identification Type",
                                                     store=True, compute='_get_l10n_ec_identification_type')
    l10n_ec_tax_support_domain_ids = fields.Many2many(comodel_name="l10n_ec.tax.support",
                                                      string="Tax Support Domain",
                                                      compute='_get_l10n_ec_identification_type')
    l10n_ec_document_type_domain_ids = fields.Many2many(comodel_name="l10n_latam.document.type",
                                                        string="Document Type Domain",
                                                        compute='_get_l10n_ec_identification_type')
