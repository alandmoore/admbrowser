"""The default message strings/templates"""

# You can override this string with the "page_unavailable_html" setting.
# Just set it to a filename of the HTML you want to display.
# It will be formatted agains the configuration file, so you can
# include any config settings using {config_key_name}

DEFAULT_404 = """<h2>Sorry, can't go there</h2>
<p>This page is not available on this computer.</p>
<p>You can return to the <a href='{start_url}'>start page</a>,
or wait and you'll be returned to the
<a href='javascript: history.back();'>previous page</a>.</p>
<script>setTimeout('history.back()', 5000);</script>
"""

# This text will be shown when the start_url can't be loaded
# Usually indicates lack of network connectivity.
# It can be overridden by giving a filename in "network_down_html"
# and will be formatted against the config.

DEFAULT_NETWORK_DOWN = """<h2>Network Error</h2>
<p>The start page, {start_url}, cannot be reached.
This indicates a network connectivity problem.</p>
<p>Staff, please check the following:</p>
<ul>
<li>Ensure the network connections at the computer and at the switch,
hub, or wall panel are secure</li>
<li>Restart the computer</li>
<li>Ensure other systems at your location can access the same URL</li>
</ul>
<p>If you continue to get this error, contact technical support</p> """

# This is shown when an https site has a bad certificate and ssl_mode is set
# to "strict".

CERTIFICATE_ERROR = """<h1>Certificate Problem</h1>
<p>The URL <strong>{url}</strong> has a problem with its SSL certificate.
For your security and protection, you will not be able to access it from
 this browser.</p>
<p>If this URL is supposed to be reachable,
 please contact technical support for help.</p>
<p>You can return to the <a href='{start_url}'>start page</a>, or wait and
you'll be returned to the
 <a href='javascript: history.back();'>previous page</a>.</p>
<script>setTimeout('history.back()', 5000);</script>
"""

# Shown when content is requested that is not HTML, text, or
# something specified in the content handlers.

UNKNOWN_CONTENT_TYPE = """<h1>Failed: unrenderable content</h1>
<p>The browser does not know how to handle the content type
<strong>{mime_type}</strong> of the file <strong>{file_name}</strong>
 supplied by <strong>{url}</strong>.</p>"""

# This is displayed while a file is being downloaded.

DOWNLOADING_MESSAGE = """<H1>Downloading</h1>
<p>Please wait while the file <strong>{filename}</strong> ({mime_type})
downloads from <strong>{url}</strong>."""

# Tooltips for the quit button

QUIT_TOOLTIP = """Click here to quit the browser."""
RESET_TOOLTIP = (
    """Click here when you are done.  """
    """It will clear your browsing history and return you to the start page."""
)
