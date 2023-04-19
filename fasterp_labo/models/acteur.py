# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CRMMEDECININ(models.Model):
    _name = 'crm.medecin_in'
    _rec_name = 'nom'
    _description = "Médécin partenaire ayant démandé l'examen"
    #_inherits = {"res.users": "user_id"}
    _inherits = {"res.partner": "partner_id"}

    nom = fields.Char()
    qualif = fields.Char('Qualification')
    partner_id = fields.Many2one('res.partner', 'Partenaire',
                                 required=False, ondelete="cascade"
                                 ,readonly=True,states={'brouillon': [('readonly', False)]},store=True)
    user_id = fields.Many2one('res.users', 'Utilisateur', ondelete="cascade")
    sexe = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=True, )
    note = fields.Text(string="Note", required=False, )
    state = fields.Selection([('brouillon', 'Brouillon'), ('valider', 'Valider')], 'Status',default="brouillon", required=False,)
    test_ids = fields.One2many(comodel_name="crm.lab_test", inverse_name="medecin_in", string="Les Tests", required=False,)


    @api.onchange('title', 'name',)
    def _onchange_titles(self):
        self.nom = str(self.title.shortcut) + " " + str(self.name)




class CRMHOPITAL(models.Model):
    _name = 'crm.hopital'
    _rec_name = 'name'
    _description = "Formation sanitaire du Médécin"

    name = fields.Char(string="NOM ", required=True, )
    code = fields.Char(string="CODE ", required=True, )
    adresse = fields.Char(string="Adresse", required=False, )
    medecin_ids = fields.One2many(comodel_name="crm.medecin_partn", inverse_name="hopital", string="", required=False,)

class CRMPATIENT(models.Model):
    _name = 'crm.patient'
    _rec_name = 'nom'
    _description = "Détails du patient"
    _inherits = {"res.partner": "partner_id"}


    nom = fields.Char()
    partner_id = fields.Many2one('res.partner', 'Partenaire',
                                 required=False, ondelete="cascade"
                                 ,readonly=True,states={'brouillon': [('readonly', False)]},)
    sexe = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=False, )
    note = fields.Text(string="Note", required=False, )
    age = fields.Integer(string="Age", required=False, )
    state = fields.Selection([('brouillon', 'Brouillon'), ('valider', 'Valider')], 'Status',default="brouillon", required=False,)

    @api.model
    def create(self, values):
        values.update({'customer_rank': 1})
        session_self__create = super(CRMPATIENT, self).create(values)
        return session_self__create

    @api.onchange('title', 'name')
    def _onchange_title(self):
        self.nom = str(self.title.shortcut) + " " + str(self.name)

    def action_voir_facture(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [
            ('type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('partner_id', 'child_of', self.partner_id.id),
        ]
        action['context'] = {'default_type':'out_invoice', 'type':'out_invoice', 'journal_type': 'sale'}
        return action


class CRMMEDECINPART(models.Model):
    _name = 'crm.medecin_partn'
    _rec_name = 'nom'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Médécin partenaire ayant démandé l'examen"
    _inherits = {"res.partner": "partner_id"}

    nom = fields.Char()
    qualif = fields.Char('Qualification ')
    #quota = fields.Float(string="Quota(%)", required=True, )
    partner_id = fields.Many2one('res.partner', 'Partenaire',
                                 required=False, ondelete="cascade",readonly=True,states={'brouillon': [('readonly', False)]},store=True)
    sexe = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=True, )
    note = fields.Text(string="Note", required=False, )
    hopital = fields.Many2one(comodel_name="crm.hopital", string="FORMATION SANITAIRE", )
    state = fields.Selection([('brouillon', 'Brouillon'), ('valider', 'Valider')], 'Status',default="brouillon", required=False,)
    part_ids = fields.One2many(comodel_name="crm.quote", inverse_name="medecin_id", string="", required=False, domain=[('paye','=',False)])
    facture_ids = fields.Many2many('account.move',ondelete="cascade",string="Les Factures")
    f_count = fields.Integer(compute='compute_count')



    # @api.onchange('nom_p')
    # def set_upper(self):
    #     self.nom_p = str(self.nom_p).upper()
    #     return

    #@api.onchange('nom_p')
    def set_onchange_all(self):
        for rec in self:
            if rec:
                rec.nom = rec.nom +' '
        return

    @api.model
    def create(self, values):
        values.update({'supplier_rank': 1})
        session_self__create = super(CRMMEDECINPART, self).create(values)
        return session_self__create


    @api.depends('facture_ids')
    def compute_count(self):
        for record in self:
            if record.facture_ids:
                record.f_count = len(record.facture_ids)
            else:
                record.f_count = 0



    def action_voir_facture(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [
            ('type', '=', ('in_invoice')),
            ('state', '=', 'posted'),
            ('partner_id', 'child_of', self.partner_id.id),
            ('id', 'in', self.facture_ids.ids),
        ]
        action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'purchase'}
        return action

    @api.onchange('title', 'name')
    def _onchange_title(self):
        self.nom = str(self.title.shortcut) + " " + str(self.name)

    def valide(self):
        self.state = 'valider'

    """def action_voir_facture(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [
            ('type', '=', ('in_invoice')),
            ('state', '=', 'posted'),
            ('partner_id', 'child_of', self.partner_id.id),
        ]
        action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'purchase'}
        return action"""

    """def facture(self):
        value = True
        articles = self.env['crm.quote'].search([('medecin_id', '=', self.id),('paye', '=', False)])
        fact = self.env['account.move'].create({'partner_id': self.partner_id.id,
                                                'type': 'out_invoice',
                                                'auto_post': True,
                                                'invoice_date': self.date,})
        for a in articles:
            line_values = {'name': a.consultation_id.exam_id.product_id.name,
                            'account_id': False,
                            'price_unit': a.consultation_id.exam_id.standard_price,
                            'quantity': 1.0,
                            'discount': 0.0,
                            'product_uom_id': a.consultation_id.exam_id.product_id.uom_id.id,
                            'product_id': a.consultation_id.exam_id.product_id.id, }
            fact.write({'invoice_line_ids': [(0, 0, line_values)]})

        fact.action_post()
        self.facture_id = fact.id
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_invoice_tree')
        value = {
                'domain': str([('id', '=', self.facture_id.id)]),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': False,
                'views': [(form_view and form_view.id or False, 'form'),
                          (tree_view and tree_view.id or False, 'tree')],
                'type': 'ir.actions.act_window',
                'res_id': self.facture_id.id,
                'target': 'current',
                'nodestroy': True
            }
        return value"""
