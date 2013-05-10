r.betamode = {
   noticeTemplate: _.template(
         '<div class="beta-notice">'
       +     'testing: <%- beta.title %>'
       +     '<a href="<%- beta.feedback_sr %>" target="_blank">give feedback</a>'
       +     '<a class="beta-disable" data-beta-name="<%- beta.name %>" href="javascript:void(0)">disable</a>'
       + '</div>'
   , null, {variable: 'beta'}),

   init: function() {
      // only display the beta notice on pages with the reddit header
      if (r.config.beta && $('#header-img').length) {
         $('body').append(this.noticeTemplate(r.config.beta))
      }

      $('#beta-settings .beta-enable').on('click', function() {
         r.betamode.enable($(this).data('beta-name'))
         r.betamode.navigateHome()
      })
      $('#beta-settings .beta-disable, .beta-notice .beta-disable').on('click', function() {
         r.betamode.disable($(this).data('beta-name'))
         r.betamode.navigateHome()
      })

      // if we're on the disable passthrough page, auto-disable.
      if ($('.content#beta-disable').length) {
         if (r.config.beta) {
            this.disable(r.config.beta.name)
         }
         this.navigateHome()
      }
   },

   enable: function(betaName) {
      $.cookie('beta_' + betaName, '1', {
         domain: r.config.cur_domain,
         path:'/',
         expires: 7
      })
   },

   disable: function(betaName) {
      $.cookie('beta_' + betaName, null, {
         domain: r.config.cur_domain,
         path:'/'
      })
   },

   navigateHome: function() {
      window.location = '//' + r.config.cur_domain
   }
}

$(function() {
   r.betamode.init()
})
