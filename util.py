import fcntl
import re

# Proxy object around a locked file that ensures it's unlocked on __exit__.
class LockedFile(object):
    def __init__(self, f): self.f = f
    def __enter__(self): return self.f
    def __exit__(self, type, value, traceback): unlock_and_close(self.f)
    def __getattr__(self, name): return object.__getattribute__(self, name)
def lock_and_open(filename, mode):
    f = open(filename, mode)
    fcntl.lockf(f.fileno(), fcntl.LOCK_EX)
    return LockedFile(f)
def unlock_and_close(f):
    fcntl.lockf(f.fileno(), fcntl.LOCK_UN)
    f.close()

# Format dates/times in a sensible way which puts leading zeros in the right places.
def my_strftime(dt, format_string):
    return \
        format_string \
        .replace("%Y", "%04i" % dt.year) \
        .replace("%m", str(dt.month)) \
        .replace("%d", str(dt.day)) \
        .replace("%A", ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')[dt.weekday()]) \
        .replace("%H", str(dt.hour)) \
        .replace("%I", str(dt.hour) if dt.hour <= 12 else str(dt.hour-12)) \
        .replace("%M", "%02i" % dt.minute)

# Some utilities for parsing SSV files.

# Splits a line in a semicolon-separated value file in which semicolons
# may be escaped by '\'.
ssv_regex = re.compile(r";((?:(?:\\;)|[^\\;])*)")
def split_ssv_line(line):
    r = re.findall(ssv_regex, ';' + line.rstrip('\r\n')) # Note that strip interprets the string
                                                         # as a list of chars, so this /will/ strip
                                                         # UNIX line endings as well as Windows.
    return r

blank_or_comment_regex = re.compile(r"^\s*(?:#.*)|(?:\s*)$")
def is_blank_or_comment(line):
    return re.match(blank_or_comment_regex, line)
