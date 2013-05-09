from datetime import datetime, timedelta

from pylons import g, c, request, response
from pylons.i18n import _

from r2.controllers import add_controller
from r2.controllers.reddit_base import (
    RedditController,
    prevent_framing_and_css,
    DELETE as DELETE_COOKIE,
)
from r2.lib import authentication
from r2.lib.base import abort
from r2.lib.hooks import HookRegistrar
from r2.lib.pages import Reddit, BoringPage
from r2.lib.template_helpers import get_domain
from r2.lib.utils import UrlParser
from r2.lib.validator import validate, VPrintable, VUser
from pages import BetaNotice, BetaSettings, BetaDisable


hooks = HookRegistrar()


def beta_user_exempt(user):
    """Check if the current user is exempt from beta access restrictions."""
    if user.name in g.beta_allowed_users:
        return True

    if user.name in g.admins:
        return True


def beta_user_allowed(user):
    """Check if the current user is permitted to access the beta."""

    if beta_user_exempt(user):
        return True

    if g.beta_require_admin:
        # admins are exempted above
        return False

    if g.beta_require_gold and not user.gold:
        return False

    return True


def redirect_to_host(hostname, path=None):
    """Redirect (302) to the specified path and host."""
    if path is None:
        path = request.path

    u = UrlParser(path)
    u.hostname = hostname
    abort(302, location=u.unparse())


class ConfigurationError(Exception): pass


# add beta cookie / gating to all requests
@hooks.on('reddit.request.begin')
def request_start():
    cookie_name = 'beta_' + g.beta_name
    c.beta = g.beta_name if cookie_name in c.cookies else None

    if not c.beta and request.host != g.beta_domain:
        # a regular site url without a beta cookie got sent to a beta app.
        # this is a configuration error that should not happen in practice, and
        # can cause redirect loops if we're not careful.
        raise ConfigurationError('request missing beta cookie')

    # run our own authentication check to sidestep c.user overrides such as the
    # logged-out override for JSONP.
    user = authentication.cookie()
    user_allowed = user and beta_user_allowed(user)

    if request.path.startswith('/beta'):
        if request.host != g.beta_domain:
            # canonicalize /beta urls to beta domain for clarity.
            redirect_to_host(g.beta_domain)
    else:
        if request.host == g.beta_domain:
            # redirect non-/beta requests on the beta domain to default domain.
            #
            # note: this redirect might result in a loop if the request on the
            # default domain is also served by this beta app, which is one
            # reason we strictly check and throw an error if this is the case
            # above.
            redirect_to_host(get_domain(subreddit=False))

        if not user_allowed:
            # they have a beta cookie but are not permitted access.
            # redirect to /beta/disable/NAME, which will delete the cookie.
            redirect_to_host(g.beta_domain, '/beta/disable')

        # extend cookie duration for a week
        c.cookies[cookie_name].expires = datetime.now() + timedelta(days=7)
        c.cookies[cookie_name].dirty = True


# clear beta cookie when logging out
@hooks.on('reddit.request.end')
def request_end():
    session_cookie = c.cookies.get(g.login_cookie)
    if session_cookie and session_cookie.expires == DELETE_COOKIE:
        cookie_name = 'beta_' + c.beta
        beta_cookie = c.cookies.get(cookie_name)
        if beta_cookie:
            response.set_cookie(
                key=cookie_name,
                value='',
                domain=beta_cookie.domain,
                expires=DELETE_COOKIE,
            )


# add beta property to js r.config
@hooks.on('js_config')
def beta_js_config(config):
    if c.beta:
        config['beta'] = {
            'name': g.beta_name,
            'title': g.beta_title,
            'feedback_sr': g.beta_feedback_sr,
        }


Reddit.extra_stylesheets.append('betamode.less')


@add_controller
class BetaModeController(RedditController):
    @prevent_framing_and_css()
    @validate(
        VUser(),
        name=VPrintable('name', 15),
    )
    def GET_beta(self, name):
        user_exempt = beta_user_exempt(c.user)

        if name != g.beta_name or (g.beta_require_admin and not user_exempt):
            abort(404)

        content = BetaSettings(
            beta_name=g.beta_name,
            beta_title=g.beta_title,
            description_md=g.beta_description_md[0],
            feedback_sr=g.beta_feedback_sr,
            enabled=c.beta,
            require_gold=g.beta_require_gold and not user_exempt,
            has_gold=c.user_is_loggedin and c.user.gold,
        )

        return BoringPage(
            pagename=g.beta_title,
            content_id='beta-settings',
            content=content,
            show_sidebar=False,
        ).render()

    @prevent_framing_and_css()
    def GET_disable(self, **kwargs):
        # **kwargs included above to swallow pylons env arguments passed in
        # due to argspec inspection of decorator **kwargs.

        return BoringPage(
            pagename=_('disabling beta'),
            content_id='beta-disable',
            content=BetaDisable(),
            show_sidebar=False,
        ).render()
