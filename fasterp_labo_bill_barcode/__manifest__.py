# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech (<https://www.iTech.com.eg>).                 #
#                                                                           #
#############################################################################

{
    'name': 'fasterp_labo bill barcode',
    'version': '13.0.1.0.0',
    'category': 'Accounting',
    'summary': """ This modules enables print invoice/bill code128 barcode as its name and add QR for invoice/bill URL""",
    'description': """    invoice/bill reports with code128 barcode reflect invoice/bill code and QR code for its URL    """,
    'author': "ISOTEN consulting & programming",
    'company': 'ISOTEN',
    'maintainer': 'ISOTEN',
    'website': "http://www.itech.com.eg",
    'depends': ['base','fasterp_labo'],
    'data': [
        'views/res_config_settings_views.xml',
        'reports/invoice_report_barcode_fasterp_labo_fact_multi.xml',
        'reports/invoice_report_barcode_fasterp_labo.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
