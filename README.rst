============
 ADMBrowser
============

Author:  Alan D Moore (http://www.alandmoore.com, e-mail me_AT_alandmoore_DOT_com)

Contributors:

- Isaac "hunternet93" Smith (isaac@isrv.pw)


Description
===========

ADMBrowser is a browser specifically for use on web kiosks.  It's based on pyqt and QWebEngine (Blink), and is designed to make lock-down very simple and painless.

It was originally conceived for use in library catalog terminals, when it became clear that browsers with ever-growing feature lists like Firefox and Chrome were too much work to lock down correctly and completely.  It was also designed to be easily configurable using a simple text file that can be hand-edited in a terminal over ssh across a slow WAN, so no databases, XML, or crazy binaries here.

ADMBrowser is a fork of WCGBrowser, with these key differences:

- WCGBrowser was based on QtWebKit, ADMBrowser is based on QtWebEngine
- WCGBrowser supports Python2 and Python3.  ADMBrowser will only actively support Python3.
- WCGBrowser runs with Qt4 or Qt5.  ADMBrowser requires Qt5 (5.4 or higher).
- The command line and configuration syntax may differ slightly.

*ADMBROWSER IS CURRENTLY ALPHA QUALITY*  Many features are broken or unavailable simply because QtWebEngine is young and does things differently than QtWebKit.


Features
========

- Blink (Chrome/Chromium) rendering
- Text-based, YAML configuration
- (Optional) Inactivity timeout
- Popups/open-in-new-window can be disabled
- Minimal, no-clutter interface simple for the general public.
- Configurable navigation bar with bookmarks
- Configurable handling of external MIME-types (PDF, etc)
- (Optional) Whitelisting of hosts & domains
- 'Screensaver' mode to display a specified URL when idle
- Printing support
- Customizable error screens
- Much, much more...

Requirements
============

- Python 3
- PyQT5 (v.5.5 or higher)
- Python YAML library (http://pyyaml.org)

It should work on any platform, but it's only been tested on Arch Linux.  

Usage
=====

The included admbrowser.yaml file shows a documented example configuration.  To use it,  copy it to /etc/admbrowser.yaml, ~/.admbrowser.yaml, or specify it with the -c (--config-file) switch.  You can make the browser.py executable, or launch it using python, like so::

    python browser.py

At a minimum, you need to specify a "start url" using either the config file or the "-l" switch, or else the browser isn't much use.  Advanced configuration is probably best done in the configuration file, but many basic features can be enabled or disabled at the command line using these switches:

====================    =====================================================================================================================================
 Switch                 Description
====================    =====================================================================================================================================
--debug_log             Send debugging output to specified file
--size                  Set the initial window size as "<width>x<height>" (e.g. "800x600"), "max" for maximized, or "full" for full-screen.
--proxy_server          Set the proxy server host and port, in the form <host>:<port>
-c, --config-file       Specify a configuration file to use
-d, --debug             Provide debugging output to stdout
-e, --allow_external    Allow the browser to open content in external programs via MIME type
-g, --allow_plugins     Allow the use of plugins like Flash, Java, etc.
-h, --help              Show quick help on command line syntax
-i, --icon-theme        The icon theme to use.  You'll need to install these themes yourself
-l, --url               The "start location" for the browser.  This is the initial URL it will load, and where it will return when reset.
-n, --no-navigation     Turn off the navigation panel (back, forward, home, shortcuts, etc).  Make sure your actual web application is fully navigable!
-p, --popups            Enable the creation of new windows when a link is clicked that opens in a new window, or javascript tries to open a window
-t, --timeout           The timeout for the inactivity monitor.  After this many seconds of inactivity, reset the browser
-u, --user	        Set the default username to be sent when a site requests authentication
-w, --password	        Set the default password to be sent when a site requests authentication
-z, --zoom              The default zoom factor for content.  0 ignores this.  1 is default, 2 would be double size, 0.5 would be half-size, etc.
====================    =====================================================================================================================================

ADMBrowser also accepts the built-in Qt command-line arguments, which provide some low-level overrides.  Documentation of these switches can be found at http://doc.qt.digia.com/qt/qapplication.html#QApplication.

Configuration File
==================

The sample configuration file is fully commented, and should be pretty easy to configure if you just read through it.  In case you just want to start from scratch, here are the current configuration options available for the application.

====================== ===============    ===============================================================================================================================================================================================================================================================
Option Name            Default Value      Explanation
====================== ===============    ===============================================================================================================================================================================================================================================================
allow_external_content False              *CURRENTLY BROKEN* Whether or not to allow non-html content, e.g. PDF files.  If this is true, you need to specify a content handler for the MIME type or a 404 error, "Network Error", or blank page will likely be displayed to the user.
allow_plugins          False              *CURRENTLY BROKEN* If true, enables the use of plugins like flash, java, etc.
allow_popups           False              Whether or not to allow navigation that requires opening a new browser window, such as javascript "window.open()" calls or links with a target of "_blank".  If False, the navigation will be ignored.  If true, a new window will be created as expected.
force_js_confirm       "ask"              If set to "accept" or "deny", will override any JavaScript are-you-sure-you-want-to-exit dialog boxes with the specified answer, if set to "ask" (the default) will ask the user each time.
suppress_alerts        False              If True, blocks JavaScript popup alerts from appearing, or shows them when False.
allow_printing         False              Enable printing of web pages from the context menu or toolbar.
print_settings         (empty)            Specify default printer settings, see below.
default_password       (empty)            default password to send when pages request authentication
default_user           (empty)            default username to send when pages request authentication
icon_theme             (qt5 default)      Icon theme to use for navigation icons
navigation             True               Display the navigation bar at the top (back/forward/reload/bookmarks/quit)
navigation_layout      (see below)        Sets the layout of the navigation bar.  See the detailed explanation below.
network_down_html      (empty)            The full path to a file containing HTML which will be displayed when the start_url page cannot be loaded, which probably indicates some kind of network error.
page_unavailable_html  (empty)            The full path to a file containing HTML which will be displayed when a page cannot be loaded, either because it's not accessible or blocked by security restrictions.
privacy_mode           True               *CURRENTLY BROKEN* Enable or disable "private browsing mode" on the webkit widget.
user_agent             (qt5 default)      Overrides the default user agent string.
user_css               (empty)            Sets a default CSS file applied to all pages viewed. Option accepts any URL supported by QT, i.e: "file://etc/wcg.css" or "http://example.com/style.css".
proxy_server           (empty)            Sets the proxy server string for HTTP proxy.  Takes the form "host:port", or just "host" if you want to use the default port of 8080.
quit_button_mode       reset              Just like timeout_mode, only this is the action taken when the quit button is pressed (same options)
quit_button_text       "I'm &Finished"    Text to display on the quit/reset button.  Can include an accelerator indicator (&).
screensaver_url        about:blank        The URL to visit when idle.  Only matters when timeout_mode is 'screensaver' and 'timeout' is nonzero.
ssl_mode               strict             *CURRENTLY BROKEN* Defines how the browser handles ssl certificate errors.  "strict" will just give an error and prevent access to the problematic URL.  "ignore" will silently ignore the errors and allow access.
start_url              about:blank        The starting URL or "home page"
stylesheet             (empty)            Filename of a qss stylesheet to use for styling the application window.  See example file.
timeout                0                  Number of seconds of inactivity before the browser closes or resets itself. A value of 0 disables the feature.
timeout_mode           reset              The action performed on inactivity timeout.  Values can be "reset" (to return to the start URL and clear history), "close" (to close the program), or 'screensaver' (to display the screensaver_url while idle)
whitelist              (empty)            A list of web domains or hosts to allow access to (see below).
window_size            "max"              Make the window default to this size.  Can be <width>x<height> (e.g. 800x600), 'max' for maximized, or "full" for fullscreen.
zoom_factor            1.0                The amount of zoom applied to pages.  .5 is half size, 2.0 is double size, etc.
====================== ===============    ===============================================================================================================================================================================================================================================================

Bookmarks
---------

Bookmarks are created in a YAML list called "bookmarks" with this format::

    bookmarks:
      1:
        name: "Bookmark Name"
        url: "http://bookmark.url/"
        description: "A short description of the bookmark, for the tooltip"

      2:
        name: "Another bookmark name":
        url: "http://example.com/some_bookmark"
        description: "A short description of this bookmark"

Bookmark names can include an ampersand to specify an accelerator key.  You can also specify bookmark entries like so::

    bookmarks:
      "Bookmark Name":
        url: "http://bookmark.url/"
        description: "A short description of the bookmark, for the tooltip"

This is more compact, but the downside is that you have no control over the order of the bookmarks (they are ordered by key, so it'll be alphabetical by name).  This mode is really for backwards compatibility, but if you have a lot of bookmarks that you want alphabetized and want to save some typing, this may be the way to go.

Content Handlers
----------------

*CURRENTLY BROKEN*

If you're allowing external content to be launched, the "content_handlers" array allows you to specify in which programs the external content will open by MIME type.
The syntax looks like this::

    content_handlers:
      "application/pdf": "xpdf"
      "application/vnd.oasis.opendocument.text":"libreoffice"

ADMBrowser will download the file to a temp directory and pass it as an argument to whatever command you specify in the second column.
Be aware of this, as in some cases you might want to write a wrapper script of some sort to deal with some types of files or programs that don't properly deal with arguments.


Navigation Layout
-----------------

The "navigation_layout" parameter is a list of items to place on the navigation bar, if it's showing.  You can choose from the following:

- "back", "forward", "refresh", "stop":  the traditional browser navigation buttons.
- "print": a button to open the print dialog for the main page.
- "zoom_in", "zoom_out":  the zoom buttons
- "bookmarks":  your bookmark buttons
- "quit":  your "I'm finished" button
- "separator": A vertical line to separate sections
- "spacer": an expanding spacer to push widgets around

The list can be specified in any valid YAML list format, but I recommend enclosing it in square braces and separating with commas.
"separator" and "spacer" can be used as many times as you wish, the others should only be used once each.

Whitelist
---------

The whitelist feature is added as a convenience to help lock down your kiosk when you don't have complete control over all the links on your kiosk pages and want to prevent users from going off to strange sites.  It's *not* a firewall or content filter, and may not behave exactly how you expect it to; so if you plan to use it, please read a bit about what it does and what it does not do.

If you don't want to use the whitelist feature, just comment it out, leave the list empty, or give it a value of "False".

What the whitelist does
~~~~~~~~~~~~~~~~~~~~~~~

You give the whitelist a list of *domains* or *hosts*, like this::

    whitelist: ["somehost.example.com", "some-local-host", "mydomain.org"]

Whenever the user clicks a link or otherwise tries to navigate to a page, the hostname is extracted from the requested URL and matched against the whitelist.  If there's a match, the page is displayed; if not, the error text is shown.

Some things are automatic:

- The start_url host is automatically whitelisted
- Bookmark hosts are automatically whitelisted
- Subdomains are also automatically whitelisted.  Thus, if you whitelist "example.com", then "foo.example.com" will be whitelisted as well (though "foo-example.com" will not, since that's actually a different domain).

If you just want to whitelist the start_url and bookmark urls and nothing else, you can just do this in the config::

    whitelist: True

When relying on the automatic whitelisting, it's important to understand that the complete *host* string of these URLs is whitelisted.  So for example, if your start_url is "http://example.com", "example.com" will be added to the whitelist (and thus all subdomains of example.com, such as foo.example.com, bar.example.com, etc.).  If you specify "http://www.example.com" as the start_url, though, "www.example.com" is added to the whitelist.  Thus, "foo.example.com" would *not* be whitelisted.

Also note that if you whitelist a URL that just forwards you to another host, you need to specify both hosts in the whitelist.

What the whitelist doesn't do
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The whitelist does not block **content** on a whitelisted page from being displayed, regardless of where the content is hosted.  As long as the page's URL is acceptable, all the content is displayed.  So, for example, if you have your images and scripts (or ads!) on a separate content delivery network, you don't need to whitelist that server.  You only need to whitelist hosts/domains of URLs to which the user is explicitly navigating (via hyperlink, bookmark, javascript forward, etc) -- in other words, the URL that would show up in a normal browser's location bar.
- The whitelist cannot take an actual path or filename, nor does it check the port, protocol, username, or any other component of the URL other than the host or domain.  Sorry.
- If you whitelist a host, its IP will *not* be automatically whitelisted (and vice-versa); nor will a fully-qualified hostname in the whitelist automatically whitelist the hostname by itself (or vice-versa).  A url is *only* allowed when its literal hostname matches a whitelist entry.

Screensaver Mode
----------------

The screensaver mode is a special timeout mode that lets you display a given URL only while the browser is idle.  Consider a configuration like this::

    start_url: 'http://example.com/kiosk'
    timeout: 1800
    timeout_mode: 'screensaver'
    screensaver_url: 'http://example.com/slides'

This configuration would do the following:

- The browser will start on http://example.com/kiosk
- After 30 minutes of no user activity (mouse/keyboard/touchscreen/etc), the navigation bar will hide and http://example.com/slides will be displayed.
- As soon as a user steps up and generates activity (moves a mouse, touches the screen, etc), the navigation bar (if configured) will reappear, and the browser will load http://example.com/kiosk.

The screensaver_url could be, for example, an image rotator, a page with ads, a welcome message, etc.  It doesn't really matter, but keep in mind the user can't actually interact with the screensaver page, because as soon as they touch a mouse or keyboard, the start_url will load.

Proxy Server
------------

ADMBrowser will allow you to set a host (name or IP) and port number for an HTTP proxy.  HTTPS, FTP, SOCKS, or authenticated proxy is not currently supported.  You can set the proxy settings one of three ways:

- The environment variable "http_proxy" is respected
- The CLI switch --proxy_server
- The configuration file option "proxy_server"

To set the proxy server, use the format "host:port", as in these examples::

    proxyserver.mynetwork.local:3128
    localhost:8080
    192.168.1.1:8880

If you neglect to include a port, and just put an IP address or hostname, the port 8080 will be used by default.

**NOTE** This feature may not work on some OS. It currently relies on setting the http_proxy environment variable (regardless of which method you use to configure it), which may not be respected on all systems.  It definitely works on Linux, and probably on any unixlike system.


Print Settings
--------------

ADMBrowser supports configuring default printer settings and allows printing without showing a dialog box. Options are set with the "print_settings" variable. For example::

    print_settings:
        silent: True
        margins: [5, 5, 3, 3]
        orientation: "landscape"

The following options are supported:

====================== ===============    ===============================================================================================================================================================================================================================================================
Option Name            Default Value      Explanation
====================== ===============    ===============================================================================================================================================================================================================================================================
silent                 False              When True, ADMBrowser will print immediately without showing the printing dialog box.
orientation            "portrait"         Specifies printing in portrait or landscape orientation.
size_unit              "millimeter"       Specifies what unit of measure used by the paper_size and margin variables. Can be "millimeter", "point", "inch", "pica", "didot", "cicero", or "devicepixel".
margins                (printer default)  Specifies the printer margins as a list in the form: [left, top, right, bottom]. Example: [5, 3.5, 6, 2.4]. Units are specified by the size_unit variable.
paper_size             (printer default)  Specifies the paper size as a list in the form: [width, height]. Example: [500, 650.5]. Units are specified by the size_unit variable.
resolution             (printer default)  Specifies the printer's resolution in ppi (pixels per inch).
mode                   "screen"           Sets what resolution the printer will use, "screen": the screen's resolution (the default) or "high": the printer's maximum resolution
====================== ===============    ===============================================================================================================================================================================================================================================================

Bugs and Limitations
====================

- There is no password dialog when a page requests authentication.  You can set a single user/password set in the config file to be sent whenever a site does request it, or provide auth credentials in the URL (in a bookmark/start_url).

If you find bugs, please report them as an "issue" at the project's github page: http://github.com/alandmoore/admbrowser/issues. If your "bug" is really a feature request, see below.

The following issues showed up with the port from QtWebKit to QtWebEngine:

- "privacy_mode" doesn't work.  The option to enable privacy mode no longer exists in QtWebEngine.
- Plugins don't work at all.  There is no Flash support whatsoever, because QtWebEngine doesn't support NPAPI plugins and doesn't include Pepper Flash.
- The handling of downloaded files is all broken.  There's not yet a way to do this in QtWebEngine (supposed to arrive in Qt5.5)
- Certificate Errors result in the page just not loading.  No errors are logged or anything.  This is due to QtWebEngine behavior, hopefully it will be fixed in future versions of the library.
- Probably much more that hasn't been tested yet.


Contributing
============

Contributions are welcome, so long as they are consistent with the spirit and intent of the browser -- that is, they are features useful in a kiosk, signage, or other lock-down situation, and keep the browser simple to configure.  I would also prefer that changes to features or behavior are opt-in (require a switch to enable them), unless it just makes no sense to do it that way.

Coding Standards
----------------

If you're contributing code, please follow these best practices:

- Follow PEP8; use a linter/checker like pyflakes, pep8, or pylint and
  make sure your code doesn't generate errors.
  
  - This includes the 79 character limit.  Yes, I'm like that.
  - Use snake_case variables, not camelCase (except for PyQt stuff we can't change)
  - Use .format() rather than the old printf-style (%) substitution
  - Remember that code should work in Py3.x with pyqt5

- Please document per PEP257; functions & classes need a docstring.
- Fork the project on GitHub, make your changes, and submit a pull request.
  You will probably be asked to change or fix some things, that's just how it goes.
    
    
  
Making Feature Requests
=======================

If there are features you'd like to see supported in this project, you have three options to see them implemented:

- Write the code (or have it written by someone else) and submit it to the project as a pull request.
- Contact me and offer to sponsor the development of the feature.  My rates are reasonable and negotiable.
- Keep your fingers crossed and hope that somebody else does one of the previous two things for the feature you want.


License
=======

ADMBrowser is released under the terms of the GNU GPL v3.
