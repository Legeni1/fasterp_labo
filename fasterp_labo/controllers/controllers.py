# -*- coding: utf-8 -*-
from odoo import http

# class MdcLab(http.Controller):
#     @http.route('/medical_lab/medical_lab/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/medical_lab/medical_lab/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('medical_lab.listing', {
#             'root': '/medical_lab/medical_lab',
#             'objects': http.request.env['medical_lab.medical_lab'].search([]),
#         })

#     @http.route('/medical_lab/medical_lab/objects/<model("medical_lab.medical_lab"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('medical_lab.object', {
#             'object': obj
#         })