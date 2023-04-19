from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CRMCATEGORY(models.Model):
    _name = 'crm.category'
    _description = "Catégorie d'éxamens"

    name = fields.Char(string="Categorie", required=False, )
    exam_ids = fields.One2many(comodel_name="crm.examen", inverse_name="category_id", required=False, )

class CRMEXAMEN(models.Model):
    _name = 'crm.examen'
    _rec_name = 'nom'
    _description = "EXAMEN "
    _inherits = {"product.product": "product_id"}
    _sql_constraints = [
	    ('name_uniq', 'unique (code)', _('Ce Code éxiste déja!')),
	]

    nom = fields.Char()
    code = fields.Char('Référence',size=4,required=True)
    #quota = fields.Float(string="Quota(%)", required=True, )
    product_id = fields.Many2one('product.product', 'Article',
                                     required=True, ondelete="cascade",
                                     readonly=True,states={'brouillon': [('readonly', False)]},)
    rendu_ids = fields.One2many(comodel_name="crm.compte_rendu", inverse_name="exam_id", string="", required=False, )
    category_id = fields.Many2one(comodel_name="crm.category", string="Type d'examen", required=True, )

    @api.onchange('code', 'name')
    def _onchange_nom(self):
        self.nom = str(self.code) + " " + str(self.name)

    @api.constrains('standard_price')
    def _price(self):
        for record in self:
            if record.standard_price >= record.lst_price:
                raise ValidationError(("La quote-part ne peut être supérieur au prix de l'examen "))


    """@api.onchange('quota','lst_price')
    def _onchange_quota(self):
        for rec in self:
            rec.standard_price = (rec.lst_price/100)*rec.quota"""

    @api.model
    def create(self, values):
        values.update({'type': 'service'})
        session_self__create = super(CRMEXAMEN, self).create(values)
        return session_self__create

class CRMCOMPTERENDU(models.Model):
    _name = 'crm.compte_rendu'
    _rec_name = 'nom'
    _description = "COMPTE RENDU D'EXAMEN"
    _sql_constraints = [
	    ('name_uniq', 'unique (code)', _('Ce Code éxiste déja!')),
	]
    nom = fields.Char()
    code = fields.Char('Référence',size=4,required=True)
    name = fields.Char(string="DÉSIGNATION", required=True, )
    exam_id = fields.Many2one(comodel_name="crm.examen", string="EXAMEN", required=True, )
    resultat = fields.Text(string="RÉSULTAT", required=True, )
    conclusion = fields.Text(string="CONCLUSION", required=False, )
    technique = fields.Text(string="TECHNIQUE", required=False, )

    category_id = fields.Many2one(comodel_name="crm.category", string="Type d'examen", related='exam_id.category_id' )

    @api.onchange('code', 'name')
    def _onchange_nom(self):
        self.nom = str(self.code) + " " + str(self.name)


"""class CRMCONCLUSION(models.Model):
    _name = 'crm.conclusion'
    _rec_name = 'name'
    _description = 'Conclusion du Compte rendu'

    name = fields.Char(string="LIBELLÉ", required=True)
    texte = fields.Text(string="DESCRIPTION", required=False, )
    #rendu_id = fields.Many2one(comodel_name="crm.compte_rendu", string="Compte rendu", )"""
