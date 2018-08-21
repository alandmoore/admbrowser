import datetime


def make_debug(do_debug, debug_log):
    """Return a function that either logs or does nothing."""
    if do_debug or debug_log:
        def debug(message):
            """Log or print a message if the global DEBUG is true."""
            message = str(message)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            debug_message = ts + ":: " + message
            if do_debug:
                print(debug_message)
            if debug_log:
                try:
                    fh = open(debug_log, 'a')
                    fh.write(debug_message + "\n")
                    fh.close
                except:
                    print("unable to write to log file {}".format(debug_log))
    else:
        def debug(message):
            pass

    return debug
