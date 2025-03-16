import debugpy
from debugpy import breakpoint as bk
import os

# To debug something call this function and then place a breakpoint with: debugpy.breakpoint()


def start_debug_session(port : int=9013):
    debugpy.listen(("0.0.0.0", port))
    debugpy.wait_for_client()
