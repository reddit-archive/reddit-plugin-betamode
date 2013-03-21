from datetime import datetime, timedelta

from pylons import g, c, request, response
from pylons.i18n import _

from r2.controllers import add_controller
from r2.controllers.reddit_base import (
    RedditController,
    prevent_framing_and_css,
    DELETE as DELETE_COOKIE,
)
from r2.lib.base import abort
from r2.lib.pages import Reddit, BoringPage
from r2.lib import template_helpers
from r2.lib.utils import UrlParser
from r2.lib.validator import validate, VPrintable, VUser
from pages import BetaNotice, BetaSettings, BetaDisable


def beta_user_exempt():
    if c.user.name in g.beta_allowed_users:
        return True

    if c.user.name in g.admins:
        return True


def beta_user_allowed():
    if not c.user_is_loggedin:
        return False

    if beta_user_exempt():
        return True

    if g.beta_require_admin:
        return False

    if g.beta_require_gold and not c.user.gold:
        return False

    return True


def beta_redirect(dest):
    u = UrlParser(dest)
    u.hostname = g.beta_domain
    abort(302, location=u.unparse())


# add beta cookie / gating to all requests
orig_pre = RedditController.pre
def patched_pre(self, *args, **kwargs):
    orig_pre(self, *args, **kwargs)

    cookie_name = 'beta_' + g.beta_name
    c.beta = g.beta_name if cookie_name in c.cookies else None

    if (not beta_user_allowed() and
            not request.path.startswith('/beta/disable')):
        if c.beta:
            # they have a beta cookie, which needs to be removed.
            # redirect to /beta/disable/..., which will delete the cookie.
            beta_redirect('/beta/disable/' + g.beta_name)
        elif g.beta_require_admin:
            # someone without a beta cookie who isn't supposed to be here.
            # if we're in admin-only mode, be opaque.
            abort(404)

    if request.path.startswith('/beta'):
        if request.host != g.beta_domain:
            # canonicalize the url
            beta_redirect(request.path)
    elif not c.beta:
        # you need to enable the beta to access that!
        beta_redirect('/beta/about/' + g.beta_name)
    else:
        # extend cookie duration for a week
        c.cookies[cookie_name].expires = datetime.now() + timedelta(days=7)
        c.cookies[cookie_name].dirty = True
RedditController.pre = patched_pre


# add beta property to js r.config
orig_js_config = template_helpers.js_config
def patched_js_config(*args, **kwargs):
    config = orig_js_config(*args, **kwargs)
    if c.beta:
        config['beta'] = c.beta
    return config
template_helpers.js_config = patched_js_config


# add beta notice to all pages
orig_content_stack = Reddit.content_stack
@staticmethod
def patched_content_stack(*args, **kwargs):
    ps = orig_content_stack(*args, **kwargs)
    if c.beta:
        ps.push(BetaNotice(
            beta_name=g.beta_name,
            beta_title=g.beta_title,
            feedback_sr=g.beta_feedback_sr,
        ))
    return ps
Reddit.content_stack = patched_content_stack


Reddit.extra_stylesheets.append('betamode.less')


@add_controller
class BetaModeController(RedditController):
    @prevent_framing_and_css()
    @validate(
        VUser(),
        name=VPrintable('name', 15),
    )
    def GET_beta(self, name):
        if name != g.beta_name:
            abort(404)

        content = BetaSettings(
            beta_name=g.beta_name,
            beta_title=g.beta_title,
            description_md=g.beta_description_md[0],
            feedback_sr=g.beta_feedback_sr,
            enabled=c.beta,
            require_gold=g.beta_require_gold and not beta_user_exempt(),
            has_gold=c.user_is_loggedin and c.user.gold,
        )

        return BoringPage(
            pagename=g.beta_title,
            content_id='beta-settings',
            content=content,
            show_sidebar=False,
        ).render()

    @prevent_framing_and_css()
    @validate(name=VPrintable('name', 15))
    def GET_disabled(self, name):
        if name != g.beta_name:
            abort(404)

        content = BetaDisable(
            beta_title=g.beta_title,
        )

        return BoringPage(
            pagename=_('disabling beta'),
            content_id='beta-disable',
            content=content,
            show_sidebar=False,
        ).render()
