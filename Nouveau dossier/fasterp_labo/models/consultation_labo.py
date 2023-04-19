from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

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
    medecin_id = fields.Many2one(comodel_name="crm.medecin_partn", string="Recommandé par", required=True ,readonly=False,states={'annuler': [('readonly', True)]})
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
        appoint_elt=[]
        for rec in self:
            partner_id =self.env['res.partner'].create({ 'name': rec.nom_p, 'title': rec.titre.id, 'is_patient':True}) 
            patient_id =self.env['lab.patient'].create({ 
                            'title' : rec.title,
                            'patient': partner_id.id,
                            'gender' : rec.sexe_p,
                            'age': rec.age,
                            'phone': rec.phone,
                            }) 
            
            
            for line in rec.consultation_labo_line:
                if line :
                    #if line.exam_familly=='laboratory':
                    appointment_line =self.env['lab.appointment.lines'].create({ 
                        'lab_test': line.exam_id.id,
                        #'cost':line.exam_id.test_cost,                                                    
                        })
                    appoint_elt.append({ 
                        'lab_test': line.exam_id.id,
                        #'cost':line.exam_id.test_cost,                                                    
                        })
                    #appoint_elt=appointment_line
            #lab_appointment_id.appointment_lines =[(6,0,[x.id for x in appoint_elt])]
            lab_appointment_id =self.env['lab.appointment'].create({ 
                            'physician_id':rec.medecin_id.id,
                            'patient_id': patient_id.id,
                            'name': self.env['ir.sequence'].next_by_code('lab.appointment'),
                            'appointment_lines' : [(0,0,[x for x in appoint_elt])],
                            # 'category_id':line.exam_id.category_id.id,
                            #'date': rec.date,
                            # 'consultation_multi_id':rec.id,                                                        
                            })            
            if rec.rest == 0.0 or rec.prix_total == rec.advance :
                rec.state = 'facturer'
            elif rec.advance == 0.0 and rec.contract_type !='post_payment' :
                rec.state = 'contract'
            elif rec.rest > 0.0 or  rec.prix_total > rec.advance :
                rec.state = 'partiel'

        return True

    def print_fact(self):
        for rec in self:
            return self.env.ref('fasterp_labo.action_fact_exams_multi').report_action(rec)
#--------------------------------------------------------
class LabTest(models.Model):
    _inherit = 'lab.test'
    #consultation_id = fields.Many2one(comodel_name="consultation.labo", string="Consultation labo", )
    familly = fields.Char(string="Categorie")
    tube = fields.Char(string="Turbe")

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
