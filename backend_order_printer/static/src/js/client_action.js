odoo.define('base.client_action', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require('web.session');
    var utils = require('report.utils');
    var ReportAction = require('report.client_action');

    var QWeb = core.qweb;

    ReportAction.include({
        start: function () {
            var self = this;
            this.iframe = this.$('iframe')[0];
            return Promise.all([this._super.apply(this, arguments), session.is_bound]).then(function () {
                self.$buttons = $(QWeb.render('report.client_action.ControlButtons.New', {}));
                self.$buttons.on('click', '.o_report_print', self.on_click_print);
                self.$buttons.on('click', '.o_report_print_now', self.on_click_print_now);
                self._update_control_panel();
            });
        },

        on_click_print_now: function () {
            this.iframe.contentWindow.print();
        },
    })
});