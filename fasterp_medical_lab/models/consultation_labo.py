from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime

#------------------------------------------------

class CONSULTATIONLABO(models.Model):
    _name = 'consultation.labo'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Facturation des Examens du labo"
    _order = "date DESC"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char()
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True ,readonly=True,states={'brouillon': [('readonly', False)]})
    state = fields.Selection(string="Etat", selection=[('brouillon', 'Brouillon'), ('facturer', 'Soldé'),('partiel', 'Avancé'),('annuler', 'Annulé'),('contract', 'Contrat')],
                             default='brouillon', required=False, )
    title = fields.Selection([
         ('ms', 'Mlle'),
         ('mister', 'M'),
         ('mrs', 'Mme'),
    ], string='Titre', default='mister', required=True)
    titre = fields.Many2one(comodel_name="res.partner.title", string="Partenaire" ,readonly=True,states={'brouillon': [('readonly', False)]})
    nom_p = fields.Char(string="Nom Patient", default="Patient01", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    sexe_p = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=False, )
    age = fields.Integer(string="Age", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    patient_id = fields.Many2one(comodel_name="lab.patient", string="Patient", readonly=True, )
    medecin_id = fields.Many2one(comodel_name="res.partner", string="Recommandé par", required=True ,domain=[('is_physician','=',True)],readonly=False,states={'annuler': [('readonly', True)]})
    consultation_labo_line = fields.One2many("consultation.labo.line", "consultation_id","Ligne d examens",readonly=True,states={'brouillon': [('readonly', False)]})
    phone = fields.Char(string="Tel", required=True)
    prix_total = fields.Float(string="Prix Total",store=True , compute='set_total')
    advance = fields.Float(string="Avance")
    rest = fields.Float(string="Reste", compute='set_rest')
    contract_type = fields.Selection(string="Accord de payement", selection=[('direct', 'Payement Direct'), ('partner_invoice', 'Facturation Partenaire'),('post_payment', 'Facturation Post Payé'),('other', 'Autre')],
                             default='direct', required=True, )

	

    @api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('consultation.labo')})
        session_self__create = super(CONSULTATIONLABO, self).create(values)
        return session_self__create
    
    @api.onchange('nom_p')
    def set_upper(self):
        self.nom_p = str(self.nom_p).upper()
        return
    
    @api.depends('consultation_labo_line.prix')
    def set_total(self):
        som = 0
        for line in self.consultation_labo_line:
            if line :
                som += line.prix
        self.prix_total = som
        #self.rest = self.prix_total-self.advance
        return True
    
    @api.depends('advance')
    def set_rest(self):
        self.rest = self.prix_total-self.advance
        return True
        
    def validation(self):
        #value = True/
        invoice_obj = self.env["account.move"]
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        prd_account_id = journal.default_credit_account_id.id
        for rec in self:
            partner_id =self.env['res.partner'].create({ 'name': rec.nom_p, 'title': rec.titre.id, 'is_patient':True}) 
            patient_id =self.env['lab.patient'].create({ 
                            'title' : rec.title,
                            'patient': partner_id.id,
                            'gender' : rec.sexe_p,
                            'age': rec.age,
                            'phone': rec.phone,
                            }) 
            
            lab_appointment_id =self.env['lab.appointment'].create({ 
                            'physician_id':rec.medecin_id.id,
                            'patient_id': patient_id.id,
                            'name': self.env['ir.sequence'].next_by_code('lab.appointment'),                                                        
                            })
            #-----------------------------------------
            if patient_id:
                curr_invoice = {
                    'partner_id': patient_id.patient.id,
                    # 'account_id': lab.patient_id.patient.property_account_receivable_id.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'invoice_date': str(datetime.datetime.now()),
                    'invoice_origin': "Lab Test# : " + rec.name,
                    # 'target': 'new',
                    #'lab_request': lab.id,
                    'is_lab_invoice': True,
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id
                if inv_ids:
                    journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                    prd_account_id = journal.default_credit_account_id.id
                    list_value = []
                    if rec.consultation_labo_line:
                        for line in rec.consultation_labo_line:
                            list_value.append((0,0, {
                                                    'name': line.exam_id.product_id.name,
                                                    'price_unit': line.exam_id.lst_price,
                                                    'quantity': 1.0,
                                                    'account_id': prd_account_id,
                                                    'move_id': inv_id,
                                                    'product_uom_id': line.exam_id.product_id.uom_id.id,
                                                    'product_id': line.exam_id.product_id.id, 
                                    }))
                        #print(list_value)
                        inv_ids.write({'invoice_line_ids': list_value})    
            #-----------------------------------------
            
            #----------------------------------------- 
            list_value1 = []           
            for line in rec.consultation_labo_line:
                if line :
                   
                    list_value1.append((0,0,{ 
                        'lab_test': line.exam_id.id,
                        'cost':line.exam_id.test_cost,
                                                                    
                        }))
            lab_appointment_id.write({'appointment_lines': list_value1})
         
            if rec.rest == 0.0 or rec.prix_total == rec.advance :
                rec.state = 'facturer'
            elif rec.advance == 0.0 and rec.contract_type !='post_payment' :
                rec.state = 'contract'
            elif rec.rest > 0.0 or  rec.prix_total > rec.advance :
                rec.state = 'partiel'

        return True
 
   
   
    

    def print_fact(self):
        for rec in self:
            return self.env.ref('fasterp_medical_lab.action_fact_exams_labo_multi').report_action(rec)
#--------------------------------------------------------

class CONSULTATIONLABOLINE(models.Model):
    _name = 'consultation.labo.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "multilignes"
    #_order = "date DESC"

    #company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char()
    consultation_id = fields.Many2one(comodel_name="consultation.labo", string="Consultation multiples", )
    date = fields.Datetime(string="Date",related='consultation_id.date')
    code = fields.Char(string="Code", required=False, readonly=True )

    exam_id = fields.Many2one(comodel_name='lab.test', string="Examen",required=True )
    prix = fields.Float(string="Prix",related='exam_id.test_cost',store=True )
    
    exam_familly = fields.Selection(string="Famille d'Examen", selection=[('laboratory', 'Laboratiore/Analyse'), ('imagery', 'Imagerie'),],
                             default='laboratory', required=True, )

    # @api.model
    # def create(self, values):
    #     values.update({'name': self.env['ir.sequence'].next_by_code('crm.multi.consultation.line')})
    #     session_self__create = super(CONSULTATIONLABOLINE, self).create(values)
    #     return session_self__create
    
#------------------------------------------------------
class LABOCOMPTERENDU(models.Model):
    _name = 'labo.compte_rendu'
    _description = "RESULTAT DE L'EXAMEN"
    _sql_constraints = [
	    ('code_uniq', 'unique (code)', _('Ce Code éxiste déja!')),
        ('name_uniq', 'unique (nom)', _('Ce Nom éxiste déja!')),
	]
    _rec_name = 'name'
    
    name = fields.Char('ID')
    nom = fields.Char()
    code = fields.Char('Référence',size=10,required=True)
    name = fields.Char(string="DÉSIGNATION", required=True,)
    exam_id = fields.Many2one(comodel_name="lab.test", string="EXAMEN", required=True, )
    resultat = fields.Text(string="RÉSULTAT", required=True,)
    conclusion = fields.Text(string="CONCLUSION", required=False, )
    technique = fields.Text(string="TECHNIQUE", required=False, )
    
    @api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('labo.compte_rendu')})
        session_self__create = super(LABOCOMPTERENDU, self).create(values)
        return session_self__create
    
#------------------------------------------------------


class LabTest(models.Model):
    _inherit = 'lab.test'
    _description = "Lab Test"
    _rec_name = 'lab_test'
    
    consultation_id = fields.Many2one(comodel_name="consultation.labo", string="Consultation labo", )
    familly = fields.Char(string="Categorie")
    tube = fields.Char(string="Turbe")
    rendu_ids = fields.One2many(comodel_name="labo.compte_rendu", inverse_name="exam_id", string="", required=False, )
    
#--------------------------------------------------------

class LabRequest(models.Model):
    _name = 'lab.request'
    _inherit = 'lab.request'
    _rec_name = 'lab_request_id'
    _description = 'Lab Request'
    
    rendu_id = fields.Many2one(comodel_name="labo.compte_rendu", string="Compte rendu",readonly=True, compute='compute_cr' )
    resultat = fields.Text(string="RÉSULTAT", required=True,)
    conclusion = fields.Text(string="CONCLUSION", required=False, )
    technique = fields.Text(string="TECHNIQUE", required=False, )
    
    

    @api.depends('test_request')
    def compute_cr(self):
        for rec in self:
            cr_val=self.env['labo.compte_rendu'].sudo().search([('exam_id','=',rec.test_request.id)])
            if cr_val:
                rec.rendu_id=cr_val[0]
                rec.technique=cr_val[0].technique
                rec.resultat=cr_val[0].resultat
                rec.conclusion=cr_val[0].conclusion
                
    def print_test_labo(self):
        for rec in self:
            return self.env.ref('fasterp_medical_lab.actionss_compte_rendu_labo').report_action(rec)            
#---------------------------------------------------------------------------------


    


