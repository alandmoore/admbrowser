import subprocess
import re

from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw

from PyQt5 import QtPrintSupport as qtp
from PyQt5 import QtWebEngineWidgets as qtwe

from PyQt5.QtNetwork import (
    QNetworkRequest
)

from . import messages as msg
from .admwebpage import AdmWebPage


class AdmWebView(qtwe.QWebEngineView):
    """This is the webview for the application.

    It represents a browser window, either the main one or a popup.
    It's a simple wrapper around QWebView that configures some basic settings.
    """
    def __init__(self, config, parent=None, debug=None, **kwargs):
        """Constructor for the AdmWebView

        Parameters:
          - config: The application's runtime configuration
          - parent: The parent widget/window
          - debug:  The function/method for posting debug strings
        """
        super(AdmWebView, self).__init__(parent)
        self.debug = debug or (lambda x: None)
        self.kwargs = kwargs
        self.config = config
        # create a web profile for the pages
        self.webprofile = kwargs.get("webprofile")
        self.setPage(AdmWebPage(None, self.webprofile, debug=self.debug))
        self.page().force_js_confirm = config.get("force_js_confirm")
        self.settings().setAttribute(
            qtwe.QWebEngineSettings.JavascriptCanOpenWindows,
            config.get("allow_popups")
        )
        if config.get('user_css'):
            self.settings().setUserStyleSheetUrl(
                qtc.QUrl(config.get('user_css'))
            )
        # self.settings().setAttribute(
        #     QWebEngineSettings.PrivateBrowsingEnabled,
        #     config.get("privacy_mode")
        # )
        self.settings().setAttribute(
            qtwe.QWebEngineSettings.LocalStorageEnabled,
            True
        )
        # self.settings().setAttribute(
        #     QWebEngineSettings.PluginsEnabled,
        #     config.get("allow_plugins")
        # )
        # self.page().setForwardUnsupportedContent(
        #     config.get("allow_external_content")
        # )
        self.setZoomFactor(config.get("zoom_factor"))

        # add printing to context menu if it's allowed
        if config.get("allow_printing"):
            self.print_action = qtw.QAction("Print", self)
            self.print_action.setIcon(qtg.QIcon.fromTheme("document-print"))
            self.print_action.triggered.connect(self.print_webpage)
            self.page().printRequested.connect(self.print_webpage)
            self.print_action.setToolTip("Print this web page")

        # connections for admwebview
        self.page().authenticationRequired.connect(
            self.auth_dialog
        )

        # connection to handle downloads
        self.webprofile.downloadRequested.connect(
            self.handle_unsupported_content
        )
        # self.page().sslErrors.connect(
        #     self.sslErrorHandler
        # )
        self.urlChanged.connect(self.onLinkClick)
        self.loadFinished.connect(self.onLoadFinished)

    def createWindow(self, type):
        """Handle requests for a new browser window.

        Method called whenever the browser requests a new window
        (e.g., <a target='_blank'> or window.open()).
        Overridden from QWebView to allow for popup windows, if enabled.
        """
        if self.config.get("allow_popups"):
            self.popup = AdmWebView(
                self.config,
                parent=None,
                **self.kwargs
            )
            # This assumes the window manager has an "X" icon
            # for closing the window somewhere to the right.
            self.popup.setObjectName("web_content")
            self.popup.setWindowTitle(
                "Click the 'X' to close this window! ---> "
            )
            self.popup.page().windowCloseRequested.connect(self.popup.close)
            self.popup.show()
            return self.popup
        else:
            self.debug("Popup not loaded on {}".format(self.url().toString()))

    def contextMenuEvent(self, event):
        """Handle requests for a context menu in the browser.

        Overridden from QWebView,
        to provide right-click functions according to user settings.
        """
        menu = qtw.QMenu(self)
        for action in [
                qtwe.QWebEnginePage.Back,
                qtwe.QWebEnginePage.Forward,
                qtwe.QWebEnginePage.Reload,
                qtwe.QWebEnginePage.Stop
        ]:
            action = self.pageAction(action)
            if action.isEnabled():
                menu.addAction(action)
        if self.config.get("allow_printing"):
            menu.addAction(self.print_action)
        menu.exec_(event.globalPos())

    def auth_dialog(self, requestUrl, authenticator):
        """Handle requests for HTTP authentication

        This is called when a page requests authentication.
        It might be nice to actually have a dialog here,
        but for now we just use the default credentials from the config file.
        """
        self.debug("Auth required on {}".format(requestUrl.toString()))
        default_user = self.config.get("default_user")
        default_password = self.config.get("default_password")
        if (default_user):
            authenticator.setUser(default_user)
        if (default_password):
            authenticator.setPassword(default_password)

    def handle_unsupported_content(self, reply):
        """Handle requests to open non-web content

        Called basically when the reply from the request is not HTML
        or something else renderable by qwebview.  It checks the configured
        content-handlers for a matching MIME type, and opens the file or
        displays an error per the configuration.
        """
        print("handle_unsupported_content called")
        self.reply = reply
        self.content_type = self.reply.header(
            QNetworkRequest.ContentTypeHeader).toString()
        self.content_filename = re.match(
            '.*;\s*filename=(.*);',
            self.reply.rawHeader('Content-Disposition')
        )
        self.content_filename = qtc.QUrl.fromPercentEncoding(
            (self.content_filename and self.content_filename.group(1)) or
            ''
        )
        content_url = self.reply.url()
        self.debug(
            "Loading url {} of type {}".format(
                content_url.toString(), self.content_type
            ))
        if not self.config.get("content_handlers").get(str(self.content_type)):
            self.setHtml(msg.UNKNOWN_CONTENT_TYPE.format(
                mime_type=self.content_type,
                file_name=self.content_filename,
                url=content_url.toString()))
        else:
            if str(self.url().toString()) in ('', 'about:blank'):
                self.setHtml(msg.DOWNLOADING_MESSAGE.format(
                    filename=self.content_filename,
                    mime_type=self.content_type,
                    url=content_url.toString()))
            else:
                # print(self.url())
                self.load(self.url())
            self.reply.finished.connect(self.display_downloaded_content)

    def display_downloaded_content(self):
        """Open downloaded non-html content in a separate application.

        Called when an unsupported content type is finished downloading.
        """
        file_path = (
            qtc.QDir.toNativeSeparators(
                qtc.QDir.tempPath() + "/XXXXXX_" + self.content_filename
            )
        )
        myfile = qtc.QTemporaryFile(file_path)
        myfile.setAutoRemove(False)
        if myfile.open():
            myfile.write(self.reply.readAll())
            myfile.close()
            subprocess.Popen([
                (self.config.get("content_handlers")
                 .get(str(self.content_type))),
                myfile.fileName()
            ])

            # Sometimes downloading files opens an empty window.
            # So if the current window has no URL, close it.
            if(str(self.url().toString()) in ('', 'about:blank')):
                self.close()

    def onLinkClick(self, url):
        """Handle clicked hyperlinks.

        Overridden from QWebView.
        Called whenever the browser navigates to a URL;
        handles the whitelisting logic and does some debug logging.
        """
        self.debug("Request URL: {}".format(url.toString()))
        if not url.isEmpty():
            # If whitelisting is enabled, and this isn't the start_url host,
            # check the url to see if the host's domain matches.
            start_url_host = qtc.QUrl(self.config.get("start_url")).host()
            if all([
                    self.config.get("whitelist"),
                    url.host() != start_url_host,
                    str(url.toString()) != 'about:blank'
            ]):
                site_ok = False
                pattern = re.compile(str(r"(^|.*\.)(" + "|".join(
                    [re.escape(w)
                     for w
                     in self.config.get("whitelist")]
                ) + ")$"))
                self.debug("Whitelist pattern: {}".format(pattern.pattern))
                if re.match(pattern, url.host()):
                    site_ok = True
                if not site_ok:
                    self.debug("Site violates whitelist: {}, {}".format(
                        url.host(), url.toString())
                    )
                    self.setHtml(self.config.get("page_unavailable_html")
                                 .format(**self.config))
            if not url.isValid():
                self.debug("Invalid URL {}".format(url.toString()))
            else:
                self.debug("Load URL {}".format(url.toString()))

    def onLoadFinished(self, ok):
        """Handle loadFinished events.

        Overridden from QWebEngineView.
        This function is called when a page load finishes.
        We're checking to see if the load was successful;
        if it's not, we display either the 404 error (if
        it's just some random page), or a "network is down" message
        (if it's the start page that failed).
        """
        if not ok:
            start_url = self.config.get('start_url')
            start_host = qtc.QUrl(start_url).host()
            start_path = str(qtc.QUrl(start_url).path()).rstrip('/')
            failed_host = self.url().host()
            failed_path = str(self.url().path()).rstrip('/')
            if all([
                    failed_host == start_host,
                    failed_path == start_path
            ]):
                self.setHtml(self.config.get("network_down_html")
                             .format(**self.config), qtc.QUrl())
                self.debug(
                    "Start Url doesn't seem to be available;"
                    " displaying error"
                )
            else:
                self.debug(
                    "load failed on URL: {}" .format(
                        self.page().requestedUrl().toString())
                )
                self.setHtml(
                    self.config.get("page_unavailable_html")
                    .format(**self.config), qtc.QUrl()
                )
        return True

    def print_webpage(self):
        """Print the webpage to a printer.

        Callback for the print action.
        Should show a print dialog and print the webpage to the printer.
        """
        if self.print_settings.get("mode") == "high":
            printer = qtp.QPrinter(mode=qtp.QPrinter.HighResolution)
        else:
            printer = qtp.QPrinter(mode=qtp.QPrinter.ScreenResolution)

        if self.print_settings:
            if self.print_settings.get("size_unit"):
                try:
                    unit = getattr(
                        QPrinter,
                        self.print_settings.get("size_unit").capitalize()
                    )
                except NameError:
                    self.debug(
                        "Specified print size unit '{}' not found,"
                        "using default.".format(
                            self.print_settings.get("size_unit")
                        ))
                    unit = qtp.QPrinter.Millimeter
            else:
                unit = qtp.QPrinter.Millimeter

            margins = (
                list(self.print_settings.get("margins")) or
                list(printer.getPageMargins(unit))
            )
            margins += [unit]
            printer.setPageMargins(*margins)

            if self.print_settings.get("orientation") == "landscape":
                printer.setOrientation(qtp.QPrinter.Landscape)
            else:
                printer.setOrientation(qtp.QPrinter.Portrait)

            if self.print_settings.get("paper_size"):
                printer.setPaperSize(qtc.QSizeF(
                    *self.print_settings.get("paper_size")
                ), unit)

            if self.print_settings.get("resolution"):
                printer.setResolution(
                    int(self.print_settings.get("resolution"))
                )

        if not self.print_settings.get("silent"):
            print_dialog = qtp.QPrintDialog(printer, self)
            print_dialog.setWindowTitle("Print Page")
            if not print_dialog.exec_() == qtw.QDialog.Accepted:
                return False

        self.print_(printer)
        return True


# ### END ADMWEBVIEW DEFINITION ### #
