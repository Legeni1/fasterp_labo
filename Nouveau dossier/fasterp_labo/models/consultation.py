from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

#------------------------------------------------

class CRMMULTICONSUL(models.Model):
    _name = 'crm.multi.consultation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Demande de plusieurs examen"
    _order = "date DESC"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char()
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True ,readonly=True,states={'brouillon': [('readonly', False)]})
    state = fields.Selection(string="Etat", selection=[('brouillon', 'Brouillon'), ('facturer', 'Soldé'),('partiel', 'Avancé'),('annuler', 'Annulé')],
                             default='brouillon', required=False, )
    titre = fields.Many2one(comodel_name="res.partner.title", string="Partenaire", required=True ,readonly=True,states={'brouillon': [('readonly', False)]})
    nom_p = fields.Char(string="Nom Patient", default="Patient01", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    sexe_p = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=False, )
    age = fields.Integer(string="Age", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    patient_id = fields.Many2one(comodel_name="crm.patient", string="Patient", readonly=True, )
    medecin_id = fields.Many2one(comodel_name="crm.medecin_partn", string="Recommandé par", required=True ,readonly=False,states={'annuler': [('readonly', True)]})
    consultation_line = fields.One2many("crm.multi.consultation.line", "consultation_id","Ligne d examens",readonly=True,states={'brouillon': [('readonly', False)]})
    prix_total = fields.Float(string="Prix Total",store=True , compute='set_total')
    advance = fields.Float(string="Avance")
    rest = fields.Float(string="Reste", compute='set_rest')
    contract_type = fields.Selection(string="Accord de payement", selection=[('direct', 'Payement Direct'), ('partner_invoice', 'Facturation Partenaire'),('post_payment', 'Facturation Post Payé'),('other', 'Autre')],
                             default='direct', required=True, )

	

    @api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('crm.multi.consultation')})
        session_self__create = super(CRMMULTICONSUL, self).create(values)
        return session_self__create
    
    @api.onchange('nom_p')
    def set_upper(self):
        self.nom_p = str(self.nom_p).upper()
        return
    
    @api.depends('consultation_line.prix')
    def set_total(self):
        som = 0
        for line in self.consultation_line:
            if line :
                som += line.prix
        self.prix_total = som
        #self.rest = self.prix_total-self.advance
        return True
    
    @api.depends('advance')
    def set_rest(self):
        self.rest = self.prix_total-self.advance
        return True
        
    def facturation(self):
        #value = True/
        for rec in self:
            # patient = self.env['crm.patient'].create({'nom' : str(rec.titre.shortcut) + " " + str(rec.nom_p),
            #                                     'name': rec.nom_p,
            #                                     'sexe' : rec.sexe_p,
            #                                     'age': rec.age,
            #                                     'title' : rec.titre.id,})
            # rec.patient_id = patient.id
            for line in rec.consultation_line:
                if line :
                    if line.exam_familly=='imagery':
                        examen_line =self.env['crm.consultation'].create({ 
                                'nom_p': rec.nom_p,
                                'sexe_p' : rec.sexe_p,
                                'age': rec.age,
                                'titre' : rec.titre.id,
                                'medecin_id':rec.medecin_id.id,
                                'exam_id': line.exam_id.id,
                                'prix':line.prix,
                                'state' : rec.state,
                                'category_id':line.exam_id.category_id.id,
                                #'patient_id': rec.patient_id.id,
                                'consultation_multi_id':rec.id,
                                })
                        #patient.write({'name': str(rec.titre.shortcut) + " " + " " + str(rec.nom_p)+ str(rec.age),})
                        examen_line.facturation()
                        rec.patient_id = examen_line.patient_id.id
                        examen_line.patient_id.write({'name': str(rec.titre.shortcut) + " " + " " + str(rec.nom_p),})
                        line.code = examen_line.code
                    if line.exam_familly=='laboratory':
                        continue
                        partner_id =self.env['res.partner'].create({ 'name': rec.nom_p, }) 
                        patient_id =self.env['fasterp_medical_lab.lab.patient'].create({ 
                                'title' : rec.titre.id,
                                'patient': partner_id.id,
                                'gender' : rec.sexe_p,
                                'age': rec.age,
                                }) 
                        lab_appointment_id =self.env['fasterp_medical_lab.lab.appointment'].create({ 
                                    'physician_id':rec.medecin_id.id,
                                    'lab_test': line.exam_id.id,
                                    'price':line.prix,
                                    # 'lab_test' : rec.state,
                                    # 'category_id':line.exam_id.category_id.id,
                                    # 'date': rec.date,
                                    # 'consultation_multi_id':rec.id,                                                        
                                 })
                        #patient.write({'name': str(rec.titre.shortcut)
                        
                        
            if rec.rest == 0.0 or rec.prix_total == rec.advance :
                rec.state = 'facturer'
            elif rec.rest > 0.0:
                rec.state = 'partiel'

        return True

    def print_fact(self):
        for rec in self:
            return self.env.ref('fasterp_labo.action_fact_exams_multi').report_action(rec)
#--------------------------------------------------------

class CRMMULTICONSULLINE(models.Model):
    _name = 'crm.multi.consultation.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "multilignes"
    #_order = "date DESC"

    #company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name = fields.Char()
    consultation_id = fields.Many2one(comodel_name="crm.multi.consultation", string="Consultation multiples", )
    date = fields.Datetime(string="Date",related='consultation_id.date')
    code = fields.Char(string="Code", required=False, readonly=True )

    state = fields.Selection(string="Etat", selection=[('brouillon', 'Brouillon'), ('facturer', 'Facturé'),('annuler', 'Annulé')],
                             default='brouillon', required=False,related='consultation_id.state', )
    titre = fields.Many2one(comodel_name="res.partner.title", string="Partenaire", required= False,readonly=True,related='consultation_id.titre')
    nom_p = fields.Char(string="Nom Patient", default="Patient01", required=False,readonly=True,related='consultation_id.nom_p')
    sexe_p = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=False,related='consultation_id.sexe_p', )
    age = fields.Integer(string="Age", required=False,readonly=True,related='consultation_id.age', )
    patient_id = fields.Many2one(comodel_name="crm.patient", string="Patient", readonly=True,related='consultation_id.patient_id', )
    medecin_id = fields.Many2one(comodel_name="crm.medecin_partn", string="Recommandé par",  related='consultation_id.medecin_id', readonly=False)
    
    exam_id = fields.Many2one(comodel_name='crm.examen', string="Examen",required=True )
    prix = fields.Float(string="Prix",related='exam_id.lst_price',store=True )
    
    exam_familly = fields.Selection(string="Famille d'Examen", selection=[('laboratory', 'Laboratiore/Analyse'), ('imagery', 'Imagerie'),],
                             default='imagery', required=True, )

    # facture_id = fields.Many2one('account.move', 'Id facture',
    #                              required=False, ondelete="cascade",)

    category_id = fields.Many2one(comodel_name="crm.category", string="Type d'examen", related='exam_id.category_id' )

    @api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('crm.multi.consultation.line')})
        session_self__create = super(CRMMULTICONSULLINE, self).create(values)
        return session_self__create
    
#------------------------------------------------------

class CRMCONSUL(models.Model):
    _name = 'crm.consultation'
    _rec_name = 'code'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Demande d'examen"
    _order = "date DESC"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    noms = fields.Char()
    code = fields.Char(string="Code", required=False, readonly=True )
    state = fields.Selection(string="Etat", selection=[('brouillon', 'Brouillon'), ('facturer', 'Soldé'),('partiel', 'Non Soldé'),('annuler', 'Annulé')],
                             default='brouillon', required=False, )
    titre = fields.Many2one(comodel_name="res.partner.title", string="Partenaire", required=True ,readonly=True,states={'brouillon': [('readonly', False)]})
    nom_p = fields.Char(string="Nom Patient", default="Patient01", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    sexe_p = fields.Selection(string="Sexe", selection=[('m', 'Masculin'), ('f', 'Féminin'),], required=False, )
    age = fields.Integer(string="Age", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    patient_id = fields.Many2one(comodel_name="crm.patient", string="Patient", readonly=True, )
    medecin_id = fields.Many2one(comodel_name="crm.medecin_partn", string="Recommandé par", required=True ,readonly=False,states={'annuler': [('readonly', True)]})
    exam_id = fields.Many2one(comodel_name='crm.examen', string="Examen",required=True ,readonly=True,states={'brouillon': [('readonly', False)]})
    prix = fields.Float(string="Prix",related='exam_id.lst_price',store=True )
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True ,readonly=True,states={'brouillon': [('readonly', False)]})

    facture_id = fields.Many2one('account.move', 'Id facture',
                                 required=False, ondelete="cascade",)

    category_id = fields.Many2one(comodel_name="crm.category", string="Type d'examen", related='exam_id.category_id' )

    consultation_multi_id = fields.Many2one(comodel_name="crm.multi.consultation", string="Facture", )
    
    exam_familly = fields.Selection(string="Famille d'Examen", selection=[('laboratory', 'Laboratiore/Analyse'), ('imagery', 'Imagerie'),],
                             default='laboratory', required=True, )

    @api.onchange('titre', 'nom_p')
    def _onchange_titre(self):
        self.noms = str(self.titre.shortcut) + " " + str(self.nom_p)

    @api.onchange('nom_p')
    def set_upper(self):
        self.nom_p = str(self.nom_p).upper()
        return

    @api.model
    def create(self, values):
        values.update({'code': self.env['ir.sequence'].next_by_code('crm.consultation')})
        session_self__create = super(CRMCONSUL, self).create(values)
        return session_self__create


    def print_fact(self):
        for rec in self:
            return self.env.ref('fasterp_labo.action_fact_exams').report_action(rec)
    
    def facturation(self):
        #value = True
        patient = self.env['crm.patient'].create({'nom' : self.noms,
                                                'name': self.nom_p,
                                                'sexe' : self.sexe_p,
                                                'age': self.age,
                                                'title' : self.titre.id,})
        self.patient_id = patient.id
        test_obj = self.env['crm.lab_test']
        test_obj.create({"consultation_id" : self.id, })
        line_values = {'name': self.exam_id.product_id.name,
                        'account_id': False,
                        'price_unit': self.exam_id.lst_price,
                        'quantity': 1.0,
                        'discount': 0.0,
                        'product_uom_id': self.exam_id.product_id.uom_id.id,
                        'product_id': self.exam_id.product_id.id, }
        fact = self.env['account.move'].create({'partner_id': self.patient_id.partner_id.id,
                                                'type': 'out_invoice',
                                                'auto_post': True,
                                                'invoice_date': self.date,
                                                'invoice_line_ids': [(0, 0, line_values)]})
        fact.action_post()
        fact.action_invoice_register_payment()
        self.state = 'facturer'
        self.facture_id = fact.id
        self.env['crm.quote'].create({"consultation_id" : self.id, })
        """form_view = self.env.ref('account.view_move_form')
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

class CRMTEST(models.Model):
    _name = 'crm.lab_test'
    _rec_name = 'code'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Demande d'examen"
    _order = "date DESC"

    name = fields.Char(string="Renseignements cliniques", required=False,default="Bilan",)
    code = fields.Char(string="", required=False,related="consultation_id.code",store=True )
    consultation_id = fields.Many2one(comodel_name="crm.consultation", string="Consultation", required=True,readonly=True,states={'brouillon': [('readonly', False)]})
    ref_paye = fields.Char( string="Réf Payement",related='consultation_id.facture_id.invoice_payment_ref',store=True)
    prix = fields.Float(string="PriX",related='consultation_id.exam_id.lst_price',store=True )
    date = fields.Datetime(string="Date", required=True,  default=fields.Datetime.now,readonly=True,states={'brouillon': [('readonly', False)]})
    exam_id = fields.Many2one(comodel_name="crm.examen",  string="EXAMEN",related='consultation_id.exam_id',store=True )
    state = fields.Selection([('brouillon', 'Facturé'), ('valider', 'Realisé'), ('annuler', 'Annulé')], 'Status',default="brouillon", required=False,)
    patient_id = fields.Many2one(comodel_name="crm.patient",  string="Patient",related='consultation_id.patient_id')
    age = fields.Integer(string="Age", required=False,related='consultation_id.patient_id.age',store=True,readonly=False,)
    medecin_part = fields.Many2one(comodel_name="crm.medecin_partn",  string="Recommandé par:",related='consultation_id.medecin_id',readonly=False, store=True )#,compute='compute_medecin_part'
    medecin_in = fields.Many2one(comodel_name="crm.medecin_in",  string="Médécin Signataire",required=False )
    facture_id = fields.Many2one('account.move', 'Facture ID',related='consultation_id.facture_id',store=True)
    rendu_id = fields.Many2one(comodel_name="crm.compte_rendu", string="Compte rendu",readonly=True,states={'brouillon': [('readonly', False)]}, compute='compute_cr')
    resultat = fields.Text(store=True,readonly=False,states={'annuler': [('readonly', True)]})
    conclusion = fields.Text(store=True,readonly=False,states={'annuler': [('readonly', True)]})

    motif_annulation = fields.Char(string="Motif de l annulation", required=False)

    exam_barcode = fields.Char(string="Code bar", required=False)

    category_id = fields.Many2one(comodel_name="crm.category", string="Type d'examen", related='exam_id.category_id' )
    
    consultation_multi_id = fields.Many2one(comodel_name="crm.multi.consultation", string="Facture",related='consultation_id.consultation_multi_id' )


    def validation(self):
        if self.rendu_id:
            self.write({'state': 'valider'})
            return True
        else:
            raise ValidationError(_("Veuillez sélectionner un compte rendu"))


    def print_test(self):
        for rec in self:
            return self.env.ref('fasterp_labo.actionss_compte_rendu').report_action(rec)

    @api.depends('exam_id')
    def compute_cr(self):
        for rec in self:
            cr_val=self.env['crm.compte_rendu'].sudo().search([('exam_id','=',rec.exam_id.id)])
            if cr_val:
                rec.rendu_id=cr_val[0]
                rec.resultat=cr_val[0].resultat
                rec.conclusion=cr_val[0].conclusion

    # @api.depends('consultation_id')
    # def compute_medecin_part(self):
    #     for rec in self:
    #         rec.medecin_part = rec.consultation_id.medecin_id.id


    @api.onchange('medecin_part')
    def compute_medecin_part(self):
        for rec in self:
            rec.consultation_id.write({'medecin_id': rec.medecin_part.id})




    """@api.model
    def create(self, values):
        values.update({'name': self.env['ir.sequence'].next_by_code('crm.lab_test')})
        session_self__create = super(CRMTEST, self).create(values)
        return session_self__create"""

    @api.onchange('rendu_id')
    def _onchange_title(self):
        if self.rendu_id.resultat and self.rendu_id.conclusion:
            self.resultat = str(self.rendu_id.resultat)
            self.conclusion = str(self.rendu_id.conclusion)
        else:
            self.resultat = ""
            self.conclusion = ""

    def cancel(self):
        if self.motif_annulation:
            quotepart = self.env['crm.quote'].sudo().search([("consultation_id" ,'=', self.consultation_id.id)])
            self.facture_id.sudo().button_cancel()
            if quotepart :
                quotepart.paye_id.write({'state': 'brouillon'})
                quotepart.paye_id.unlink()
            self.write({'state': 'annuler'})
            self.consultation_id.write({'state': 'annuler'})
            return True
        else:
            raise ValidationError(_("Merci de renseigner le motif de l annulation"))
