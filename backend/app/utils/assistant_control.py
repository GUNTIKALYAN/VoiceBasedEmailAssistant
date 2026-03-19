exit_requested = False


def request_exit():
    global exit_requested
    exit_requested = True


def reset_exit():
    global exit_requested
    exit_requested = False