# -*- coding: utf-8 -*-
{
    'name': "Print Orders Directly From Backend",

    'summary': "Print Report type Html",

    'author': "TopERP Technology Solution Limited, Linh Nguyen",
    'website': "https://toperp.vn/addons/webview-print",

    'category': 'Extra Tools',
    'version': '1.0',

    'depends': ['base', 'mail'],

    'data': [
        'views/templates.xml',
    ],

    'qweb': ['static/src/xml/*.xml'],

    'images': ['static/description/icon.png'],

    'license ': 'LGPL-3',

    'installable': True,
    'auto_install': False,
    'application': True,
    # 'price': '5',
    'currency': 'EUR'
}
