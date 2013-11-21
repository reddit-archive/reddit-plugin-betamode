from r2.config.routing import not_in_sr
from r2.lib.plugin import Plugin
from r2.lib.configparse import ConfigValue
from r2.lib.js import Module

class BetaMode(Plugin):
    needs_static_build = True

    config = {
        ConfigValue.str: [
            'beta_domain',
            'beta_name',
            'beta_title',
            'beta_feedback_url',
        ],
        ConfigValue.bool: [
            'beta_require_admin',
            'beta_require_gold',
        ],
        ConfigValue.tuple: [
            'beta_allowed_users',
        ],
        ConfigValue.messages: [
            'beta_description_md',
        ]
    }

    js = {
        'reddit': Module('reddit.js',
            'betamode.js',
        )
    }

    def add_routes(self, mc):
        mc('/beta/about/:name', controller='betamode', action='beta',
           conditions={'function':not_in_sr})
        mc('/beta/disable', controller='betamode', action='disable',
           conditions={'function':not_in_sr})

    def load_controllers(self):
        from reddit_betamode import betamode
        betamode.hooks.register_all()
