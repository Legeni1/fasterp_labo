# -*- coding: utf-8 -*-
{
    'name': "fasterp_labo",

    'summary': """
        FAST ERP LABORATOIRE D'ANALYSE MÉDICALE 
        """,

    'description': """
       FAST ERP LABO  pour le  LABORATOIRE  D\'IMAGERIE D\'ANALYSE MÉDICALE 
    """,
    'author': 'BOGNI-DANCHI T.',
    'maintainer': 'BOGNI-DANCHI T.',
    'website': 'https://www.sfmtechnologies.com',
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','l10n_syscohada','fasterp_medical_lab'],

    # always loaded
    'data': [
        'security/crm_security.xml',
        'security/ir.model.access.csv',

        'report/papers.xml',
        'report/report_compte_rendu.xml',
        'report/report_quote_part.xml',
        'report/report_facture_cons.xml',
        'report/report_facture_cons_multi.xml',

        'views/acteur_view.xml',
        'views/exam_view.xml',
        'views/consultation_view.xml',
        'views/quote_view.xml',
        'views/consultation_multi_lines.xml',
        'views/consultation_labo_view.xml',
        'views/lab_test.xml',
        'views/menu.xml',

        'data/ir.sequnce_data.xml',


        # wizards
        #"wizards/view_quotas_wiz.xml",

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
