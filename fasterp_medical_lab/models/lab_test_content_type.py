# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P @ cybrosys and Niyas Raphy @ cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields,api


class LabTestContentType(models.Model):
    _name = 'lab.test.content_type'
    _rec_name = 'content_type_name'
    _description = "Content"
    _inherit = {"product.product": "product_id"}
    
    
    content_type_name = fields.Char(string="Name", required=True, help="Content type name")
    content_type_code = fields.Char(string="Code")
    parent_test = fields.Many2one('lab.test', string="Test Category")

    name = fields.Char()
    product_id = fields.Many2one('product.product', 'Article',
                                     required=True, ondelete="cascade",
                                     readonly=True)
    #cost_price=
    @api.onchange('content_type_code', 'content_type_name')
    def _onchange_nom(self):
        self.name = str(self.content_type_code) + " " + str(self.content_type_name)
        
    @api.model
    def create(self, values):
        values.update({'type': 'stockable'})
        session_self__create = super(LabTestContentType, self).create(values)
        return session_self__create


