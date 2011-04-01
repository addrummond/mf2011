#!/usr/bin/python
import sys,os,os.path
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

import web
import conf
import StringIO
import urllib
import fcntl
import time
import datetime
import re
import itertools
import types

# Proxy object around a locked file that ensures it's unlocked on __exit__.
class LockedFile(object):
    def __init__(self, f): self.f = f
    def __enter__(self): return self.f
    def __exit__(self, type, value, traceback): unlock_and_close(self.f)
    def __getattr__(self, name): return object.__getattribute__(self, name)
def lock_and_open(filename, mode):
    if os.path.exists(filename):
        f = open(filename, "r") # Open first as read-only.
        fcntl.flock(f.fileno(), 2)
        if mode != "r": # If necessary, reopen with the given mode.
            f.close()
            f = open(filename, mode)
    else:
        f = open(filename, mode)
    return LockedFile(f)
def unlock_and_close(f):
    fcntl.flock(f.fileno(), 8)
    f.close()

urls = (
    '/',              'Index',
    '/schedule',      'Schedule',
    '/speakers',      'Speakers',
    '/register',      'Register',
    '/directions',    'Directions',
    '/accommodation', 'Accommodation',
    '/main.css',      'Maincss'
)

app = web.application(urls, globals())

def my_strftime(dt, format_string):
    return \
        format_string \
        .replace("%Y", "%04i" % dt.year) \
        .replace("%m", str(dt.month)) \
        .replace("%d", str(dt.day)) \
        .replace("%A", ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')[dt.day-1]) \
        .replace("%H", str(dt.hour)) \
        .replace("%I", str(dt.hour) if dt.hour <= 12 else str(dt.hour-12)) \
        .replace("%M", "%02i" % dt.minute)

tglobs = dict(
    int=int,
    str=str,
    url_for=conf.url_for,
    websafe=web.websafe,
    my_strftime=my_strftime
)
render = web.template.render(os.path.join(BASE, 'templates/'), globals=tglobs)

def render_wrapper(title, template, js_includes=[]):
    if web.input().get('_ajax'):
        # Bit of a hack -- need to make sure they still get the additional js includes.
        jss = StringIO.StringIO()
        for inc in js_includes:
            jss.write(u'\n<script type="text/javascript" src="%s"></script>\n' % inc)
        return title + "\n" + jss.getvalue() + unicode(template)
    else:
        return render.wrapper(title, template, js_includes)

class Index(object):
    def GET(self):
        return render_wrapper('', render.index())

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

# Read speakers SSV db.
speaker_list = []
with open(os.path.join(conf.WORKING_DIR, "speakers.txt")) as speakers_f:
    for l in speakers_f:
        if not is_blank_or_comment(l):
            fields = split_ssv_line(l)
            assert len(fields) == 4
            speaker_list.append(dict(name=fields[0], institution=fields[1], homepage=fields[2], abstractfile=fields[3]))
class Speakers(object):
    def GET(self):
        return render_wrapper('Speakers', render.speakers(speaker_list))

# Read schedule SSV db.
speaker_regex = re.compile(r"^\s*\[([^]]+)\](.*)$")
blank_regex = re.compile(r"^\s*$")
event_list = []
with open(os.path.join(conf.WORKING_DIR, "schedule.txt")) as schedule_f:
    for l in schedule_f:
        if not is_blank_or_comment(l):
            fields = split_ssv_line(l)
            assert len(fields) == 3
            event = { }
            try:
                iso8601 = "%Y-%m-%dT%H:%M"
                event['start_datetime'] = datetime.datetime(*time.strptime(fields[0], iso8601)[:5])
                if not re.match(blank_regex, fields[1]):
                    event['end_datetime'] = datetime.datetime(*time.strptime(event['start_datetime'].strftime("%Y-%m-%dT" + fields[1]), iso8601)[:5])
            except ValueError, e:
                raise Exception("Error parsing date/time in schedule.txt: use ISO 8601 format (see e.g. Wikipedia article) (%s)." % str(e))
            info = fields[2]
            m = re.match(speaker_regex, info)
            if m:
                event['speaker'] = m.group(1).rstrip(' ')
                event['info'] = m.group(2)
                s = [s for s in speaker_list if s['name'] == m.group(1)]
                if len(s) < 1:
                    raise Exception("Unknown speaker referenced in schedule.txt: '%s'" % m.group(1))
                event['abstractfile'] = s[0]['abstractfile']
                event['homepage'] = s[0]['homepage']
            else:
                event['info'] = info
            event_list.append(event)
event_list.sort(key=lambda event: (event['start_datetime'], event.get('end_datetime', datetime.datetime(1, 1, 1, 1, 1))))
# Group events by day (makes table rendering logic simpler in template).
event_list_by_days = list(itertools.imap(lambda x: list(x[1]),
    itertools.groupby(event_list, lambda e: (e['start_datetime'].year,
                                             e['start_datetime'].month,
                                             e['start_datetime'].day))
))
class Schedule(object):
    def GET(self):
        return render_wrapper('Schedule', render.schedule(event_list_by_days))

class Register(object):
    JS_EXTRAS = [conf.url_for('/static/register.js'), conf.url_for('/static/jquery.simplemodal.js')]

    def GET(self):
        return render_wrapper('Register', render.register(), Register.JS_EXTRAS)

    def POST(self):
        data = web.input(friday="no", saturday="no", reception="no", crash="no")
        for k in ('name', 'aff', 'email'):
            if not data.has_key(k) or not data[k]:
                return render_wrapper('Register', render.register("You must enter your full name, affiliation and email address."), Register.JS_EXTRAS)

        try:
            with lock_and_open(os.path.join(conf.WORKING_DIR, "registrations"), "a") as f:
                f.write("--\n%s\n" % time.ctime())
	        def ersatz(s): return s.replace("%", "%25").replace("\r", "%0d").replace("\n", "%0a")
                for k in ('name', 'aff', 'email', 'friday', 'saturday', 'reception', 'crash', 'comments'):
                    f.write("%s: %s\n" % (k, ersatz(data[k]) if data.has_key(k) else ''))
                f.write('\n')
        except IOError:
            web.internalerror()

        return render_wrapper('Register', render.register_success(data))

class Directions(object):
    def GET(self):
        return render_wrapper('Directions', render.directions())

class Accommodation(object):
    def GET(self):
        return render_wrapper('Accommodation', render.accommodation())

class Maincss(object):
    def GET(self):
        web.header("Content-Type", "text/css; charset=utf-8")
        return render.main()

application = app.wsgifunc()

if __name__ == "__main__":
    app.run()
