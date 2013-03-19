# reddit beta testing mode

This plugin orchestrates an opt-in beta test on an app server running a new feature branch of reddit. The presence of a beta cookie is used to flag a frontend proxy like HAProxy to direct users to the beta server instead of the standard app server pool.


## details

To set up a beta, set up an app server with this plugin on a subdomain (such as http://lab.reddit.com) and configure your web frontend (sample HAProxy config below). Visits to the beta subdomain will be redirected to `/beta/about/NAME`, a page describing the beta and providing an opt-in button. When clicked, a JavaScript handler will create the cookie `beta_NAME` and navigate to the root domain (e.g. http://www.reddit.com). If your web frontend is configured properly, this request will be directed to the beta server.

When the beta is in place, a yellow overlay bar will be displayed allowing users to disable the beta. Clicking this button will delete the cookie and return to the root domain of the site. Beta cookies expire 7 days after the last request.

Users must be logged in to enable a beta. Beta access can be restricted to gold users or admins only. If access is restricted to admins, unauthorized requests will 404. If a user logs out or becomes ineligible for a beta (such as access restriction configuration changed), the user will be redirected to `/beta/disable/NAME`, a page which will automatically delete the cookie and then refresh. This interstitial page serves to work around browser inconsistencies setting cookies on redirects and to provide a suggestion to users to delete cookies in the case of being caught in an unforeseen redirect loop.


## ini config params

```ini
# domain name of the beta app server (don't forget to add to reserved_subdomains)
beta_domain = beta.reddit.local

# short lowercase identifier for beta (used in urls and cookies)
beta_name = maelstrom

# short human readable title for beta
beta_title = tag maelstrom beta

# markdown description for beta displayed on sign-up page
beta_description_md = "# beta test tag maelstrom\n it's folksonomy-driven!"

# subreddit to direct beta feedback to
beta_feedback_sr = /r/tagmaelstrom

# only allow gold users to enable the beta
beta_require_gold = False

# only allow admins to view and enable the beta (non-admins and logged-out will 404)
beta_require_admin = False

# list of users exempt from the above requirements
beta_allowed_users = kn0thing
```

## simple dev haproxy sample config

This config assumes you are running a standard app server on port 8001 and a beta plugin app server on port 8002.

```
global
    maxconn 100

frontend frontend 0.0.0.0:80
    mode http
    timeout client 10000
    option forwardfor except 127.0.0.1
    option httpclose

    # requests containing a beta cookie go to the beta server
    acl beta hdr_sub(Cookie) beta_maelstrom=

    # send the beta domain to the beta server for opt-in
    acl beta hdr(Host) beta.reddit.local

    use_backend beta if beta
    default_backend dynamic

backend dynamic
    mode http
    timeout connect 4000
    timeout server 30000
    timeout queue 60000
    balance roundrobin

    server app01-8001 localhost:8001 maxconn 1 check

backend beta
    mode http
    timeout connect 4000
    timeout server 30000
    timeout queue 60000
    balance roundrobin

    server app02-8002 localhost:8002 maxconn 1 check

    # if the beta app server is down for some reason, fall back to the default server.
    server app01-8001 localhost:8001 maxconn 1 check backup
```
