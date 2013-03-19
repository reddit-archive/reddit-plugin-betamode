r.betamode = {
   init: function() {
      $('#beta-settings .beta-enable').on('click', function(){
         r.betamode.enable($(this).data('beta-name'))
      })
      $('#beta-settings .beta-disable, .beta-notice .beta-disable').on('click', function() {
         r.betamode.disable($(this).data('beta-name'))
      })

      // if we're on the disable passthrough page, auto-disable.
      if ($('.content#beta-disable').length) {
         this.disable(r.config.beta)
      }
   },

   enable: function(betaName) {
      $.cookie('beta_' + betaName, '1', {domain: r.config.cur_domain, path:'/', expires:7})
      window.location = '//' + r.config.cur_domain
   },

   disable: function(betaName) {
      $.cookie('beta_' + betaName, null, {domain: r.config.cur_domain, path:'/'})
      window.location = '//' + r.config.cur_domain
   }
}

$(function() {
   r.betamode.init()
})
