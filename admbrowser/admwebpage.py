# ### ADMWEBPAGE #### #

from PyQt5.QtWebEngineWidgets import QWebEnginePage

from . import messages as msg

class AdmWebPage(QWebEnginePage):
    """Subclassed QWebEnginePage,
    representing the actual web page object in the browser.

    This was subclassed so that some functions can be overridden.
    """
    def __init__(self, config, parent=None, profile=None, debug=None):
        """Constructor for the class"""
        self.debug = debug or (lambda x: None)
        self.config = config
        if not profile:
            super().__init__(parent)
        else:
            super().__init__(profile, parent)
        debug("Profile is: {}".format(self.profile()))

    def javaScriptConsoleMessage(self, level, message, line, sourceid):
        """Handle console.log messages from javascript.

        Overridden from QWebEnginePage so that we can
        send javascript errors to debug.
        """
        self.debug('Javascript Error in "{}" line {}: {}'.format(
            sourceid, line, message)
        )

    def javaScriptConfirm(self, frame, msg):
        """Handle javascript confirm() dialogs.

        Overridden from QWebEnginePage so that we can (if configured)
        force yes/no on these dialogs.
        """
        if self.config.get('force_js_confirm') == "accept":
            return True
        elif self.config.get('force_js_confirm') == "deny":
            return False
        else:
            return super().javaScriptConfirm(self, frame, msg)

    def javaScriptAlert(self, frame, msg):
        if not self.config.get('suppress_alerts'):
            return super().javaScriptAlert(self, frame, msg)

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
                msg.CERTIFICATE_ERROR.format(
                    url=error.url().toString(),
                    start_url=self.config.get("start_url")
                ))

    def renderProcessTerminated(self, *args):
        self.debug("RenderProcessTerminated: {}".format(args))
        super().renderProcessTerminated(args)

# ### END ADMWEBPAGE DEFINITION ### #
