# ### ADMWEBPAGE #### #

from PyQt5.QtWebEngineWidgets import QWebEnginePage

from .messages import CERTIFICATE_ERROR


class AdmWebPage(QWebEnginePage):
    """Subclassed QWebEnginePage,
    representing the actual web page object in the browser.

    This was subclassed so that some functions can be overridden.
    """
    def __init__(self, parent=None, debug=None):
        """Constructor for the class"""
        super(AdmWebPage, self).__init__(parent)
        self.user_agent = None
        self.debug = debug or (lambda x: None)

    def javaScriptConsoleMessage(self, message, line, sourceid):
        """Handle console.log messages from javascript.

        Overridden from QWebEnginePage so that we can
        send javascript errors to debug.
        """
        self.debug(
            'Javascript Error in "{}" line {}: {}'
            .format(sourceid, line, message)
        )

    def javaScriptConfirm(self, frame, msg):
        """Handle javascript confirm() dialogs.

        Overridden from QWebEnginePage so that we can (if configured)
        force yes/no on these dialogs.
        """
        if self.force_js_confirm == "accept":
            return True
        elif self.force_js_confirm == "deny":
            return False
        else:
            return QWebEnginePage.javaScriptConfirm(self, frame, msg)

    def javaScriptAlert(self, frame, msg):
        if not self.suppress_alerts:
            return QWebEnginePage.javaScriptAlert(self, frame, msg)

    def userAgentForUrl(self, url):
        """Handle reqests for the browser's user agent

        Overridden from QWebEnginePage so we can force
        a user agent from the config.
        """
        return self.user_agent or QWebEnginePage.userAgentForUrl(self, url)

    def certificateError(self, error):
        """Handle SSL errors in the browser.

        Overridden from QWebEnginePage.
        Called whenever the browser encounters an SSL error.
        Checks the ssl_mode and responds accordingly.
        Doesn't seem to get called in Qt 5.4
        """
        self.debug("certificate error")
        if self.config.get("ssl_mode") == 'ignore':
            self.debug("Certificate error ignored")
            self.debug(error.errorDescription())
            return True
        else:
            self.setHtml(
                CERTIFICATE_ERROR.format(
                    url=error.url().toString(),
                    start_url=self.config.get("start_url")
                ))


# ### END ADMWEBPAGE DEFINITION ### #
