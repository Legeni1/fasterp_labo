# -*- coding: utf-8 -*-


#importation des bibliothéque necessaire pour la realisation de ce module
import base64
import time
from odoo import fields, models, api
from odoo.tools.translate import _
from datetime import datetime,date
from dateutil import relativedelta


MOIS = [
    ('1', 'Janvier'),
    ('2', 'Février'),
    ('3', 'Mars'),
    ('4', 'Avril'),
    ('5', 'Mai'),
    ('6', 'Juin'),
    ('7', 'Juillet'),
    ('8', 'Aout'),
    ('9', 'Septembre'),
    ('10', 'Octobre'),
    ('11', 'Novembre'),
    ('12', 'Décembre')]

DATE_FORMAT = "%Y-%m-%d"
DATE_FORMAT2 = "%d/%m/%Y"

class LABOQUOTE(models.Model):
    _name = 'labo.quote'
    _description = "gestion des quotes parts"
    #_inherits = {"product.product": "product_id"}
    _order = "date DESC"

    name = fields.Char()
    medecin_id = fields.Many2one(comodel_name="res.partner",
      string="Médécin Partenaire",domain=[('is_physician','=',True)],store=True )
    #product_id = fields.Many2one('product.product', 'Article',required=False, ondelete="cascade",readonly=True,states={'brouillon': [('readonly', False)]},)
    request_id = fields.Many2one(comodel_name="lab.request", string="", required=True, )
    montant = fields.Float(string="Montant",related="request_id.test_request.standard_price",store=True )
    paye = fields.Boolean(string=' Payé?',default=False)
    date = fields.Datetime( related='request_id.app_id.date',store=True )
    paye_id = fields.Many2one(comodel_name="labo.paye_quota", string="", )

    
    @api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('labo.quote')})
        session_self__create = super(LABOQUOTE, self).create(values)
        return session_self__create

class LABOPayeQuota(models.Model):
    _name = 'labo.paye_quota'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']


    name = fields.Char(readonly=True,states={'brouillon': [('readonly', False)]},store=True)
    date_from = fields.Date('Du',readonly=True,states={'brouillon': [('readonly', False)]},default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Au',readonly=True,states={'brouillon': [('readonly', False)]},default=lambda *a: str(datetime.now() + relativedelta.relativedelta(
            months=+1,
            day=1,
            days=-1))[:10])
    mois_de_paie = fields.Selection(MOIS,default='1',string="Mois de la paye",readonly=True,states={'brouillon': [('readonly', False)]})
    quota_ids = fields.One2many('labo.quote', 'paye_id', 'Quote-parts',readonly=True,states={'brouillon': [('readonly', False)]},store=True)
    state = fields.Selection(string="Etat", selection=[('brouillon', 'Brouillon'), ('valider', 'Validé'),],
                             default='brouillon', required=False, )
    rech = fields.Selection(string="Trier", selection=[('mois', 'Par Mois'), ('periode', 'Par Période'),],
                             default='periode',readonly=True,states={'brouillon': [('readonly', False)]}, required=True, )
    montants = fields.Float(string="Montant",compute="_montant_total",store=True,readonly=True,states={'brouillon': [('readonly', False)]} )
    facture_ids = fields.Many2many('account.move',string="Les Factures")
    f_count = fields.Integer(compute='compute_count')
    notes = fields.Text("Notes")


    @api.depends('facture_ids')
    def compute_count(self):
        for record in self:
            record.f_count = len(record.facture_ids)

    def action_voir_facture(self):
        self.ensure_one()
        facture = [p.partner_id.id for p in self.facture_ids]
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [
            ('type', '=', ('in_invoice')),
            ('state', '=', 'posted'),
            ('partner_id', 'in', facture),
            ('id', 'in', self.facture_ids.ids),

        ]
        action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'purchase'}
        return action

    def validation(self):
        medecins = self.mdecins()
        factures = []
        for m in medecins:
            quot = [rec for rec in self.quota_ids]
            articles = [r for r in quot if r.medecin_id == m]
            articles = m.get('quote')
            fact = self.env['account.move'].create({'partner_id': m.get('id').partner_id.id,
                                                    'type': 'in_invoice',
                                                    'auto_post': True,
                                                    'invoice_date': datetime.now(),})
            for a in articles:
                a.paye = True
                line_values = {'name': a.request_id.exam_id.product_id.name,
                                'account_id': False,
                                'price_unit': a.request_id.exam_id.standard_price,
                                'quantity': 1.0,
                                'discount': 0.0,
                                'product_uom_id': a.request_id.exam_id.product_id.uom_id.id,
                                'product_id': a.request_id.exam_id.product_id.id, }
                fact.write({'invoice_line_ids': [(0, 0, line_values)]})

            #m.get('id').facture_ids = [(0, 0, fact)]
            fact.action_post()
            factures.append(fact.id)
        self.facture_ids = [(6,0,factures)]
        pdf = self.env.ref('fasterp_medical_lab.actions_quote_parts_labo').render_qweb_pdf(self.ids)
        b64_pdf = base64.b64encode(pdf[0])
        # save pdf as attachment
        name = self.name
        self.write({'state': 'valider'})
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name + '.pdf',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
    


    def print_fact(self):
        for rec in self:
            return self.env.ref('fasterp_medical_lab.actions_quote_parts_labo').report_action(rec)

    @api.depends('quota_ids')
    def _montant_total(self):
        s = 0.0
        quotes = [q for q in self.quota_ids]
        for rec in quotes:
            s = s + rec.montant
        self.montants = s


    @api.onchange('mois_de_paie', 'date_from', 'date_to')
    def _onchange_quotas(self):
        self.quota_ids = None
        self.name = ""
        domain = []
        if self.rech == "mois" and self.mois_de_paie:
            oday = datetime.now()
            first_of_month = datetime.strptime("%s-%s-01" % (str(oday.year), str(self.mois_de_paie)),
                    DATE_FORMAT)
            lastday = (first_of_month + relativedelta.relativedelta(months=+1,day=1,days=-1))
            domain = [('date', '>=', first_of_month.strftime(DATE_FORMAT)),
                    ('date', '<=', lastday.strftime(DATE_FORMAT)),
                    ('paye', '=', False)]
            self.name = "QUOTES-PARTS DU MOIS DE "+ str(dict(self._fields['mois_de_paie'].selection).get(self.mois_de_paie)) + " " + str(oday.year)

        elif self.rech == "periode"  and self.date_from and self.date_to:
            domain = [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('paye', '=', False)]
            self.name = _("QUOTES-PARTS POUR LA PERIODE  Du " + str(self.date_from.strftime(DATE_FORMAT2))+ "  Au " + str(self.date_to.strftime(DATE_FORMAT2)))
        quotes = self.env['labo.quote'].search(domain)
        self.quota_ids = [(6,0,quotes.ids)]  

    @api.model
    def unlink(self):
        for elt in self:
            if elt.state != 'brouillon':
                raise Warning(_('Erreur! Impossible de supprimer cet élément car il n\'est en brouillon'))
        return super(LABOPayeQuota, self).unlink()

    def mdecins(self):
        med = self.env['res.partner'].search([('is_physician','=',True)])
        medecins = []
        for m in med:
            medecin = {}
            medecin['id'] = m
            quot = [rec for rec in self.quota_ids]
            quote = [r for r in quot if r.medecin_id == m]
            total = sum([r.montant for r in quote])
            medecin['total'] = total
            medecin['quote'] = quote
            medecins.append(medecin)
        meds = [m for m in medecins if len(m.get('quote')) >= 1]
        return meds
