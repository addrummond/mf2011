#!/usr/bin/python
import sys,os,os.path
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

import web
import conf
import StringIO
import urllib
import time
import datetime
import re
import itertools
import types
from util import *

# Try to import the watchdog file notification API, if it's installed.
HAVE_WATCHDOG = False
try:
    import watchdog
    import watchdog.events
    import watchdog.observers
    HAVE_WATCHDOG = True
except ImportError:
    pass

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

tglobs = dict(
    int=int,
    str=str,
    reduce=reduce,
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

blank_regex = re.compile(r"^\s*$")
def read_in_abstract(fname):
    with open(fname) as f:
        abstract_title = f.readline().rstrip()
        if not abstract_title:
            raise Exception("Couldn't get title for abstract file '%s'" % fname)
        abstract_html = f.read()
        if re.match(blank_regex, abstract_html):
            abstract_html = "" # Ensure it counts as False in conditionals.
        return abstract_title, abstract_html

# Read speakers SSV db.
speaker_list = []
def read_in_speaker_list():
    global speaker_list
    new_speaker_list = []
    with open(os.path.join(conf.WORKING_DIR, "speakers.txt")) as speakers_f:
        for l in speakers_f:
            if not is_blank_or_comment(l):
                fields = split_ssv_line(l)
                assert len(fields) == 4

                # Read in abstract.
                abstract_title = None
                abstract_html = None
                if fields[3]:
                    abstract_title, abstract_html = read_in_abstract(os.path.join(conf.WORKING_DIR, 'abstracts', fields[3]))
                new_speaker_list.append(dict(name=fields[0],
                                             institution=fields[1],
                                             homepage=fields[2],
                                             abstract_file=fields[3],
                                             abstract_title=abstract_title,
                                             abstract_html=abstract_html))
    speaker_list = new_speaker_list
read_in_speaker_list()

# Read schedule SSV db.
speaker_regex = re.compile(r"^\s*\[([^]]+)\](.*)$")
event_list_by_days = []
def read_in_event_list():
    global event_list_by_days
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
                        event['end_datetime'] = datetime.datetime(
                            *time.strptime(event['start_datetime'].strftime("%Y-%m-%dT" + fields[1]),
                                           iso8601)[:5]
                        )
                except ValueError, e:
                    raise Exception("Error parsing date/time in schedule.txt: " +
                                    "use ISO 8601 format (see e.g. Wikipedia article) (%s)." %
                                    str(e))
                info = fields[2]
                m = re.match(speaker_regex, info)
                if m:
                    event['speaker'] = m.group(1).rstrip(' ')
                    event['info'] = m.group(2)
                    s = [s for s in speaker_list if s['name'] == m.group(1)]
                    if len(s) < 1:
                        raise Exception("Unknown speaker referenced in schedule.txt: '%s'" % m.group(1))
                    event['abstract_title'] = s[0]['abstract_title']
                    event['abstract_html'] = s[0]['abstract_html']
                    event['homepage'] = s[0]['homepage']
                else:
                    event['info'] = info
                event_list.append(event)
    event_list.sort(key=lambda event: (event['start_datetime'],
                                       event.get('end_datetime', datetime.datetime(1, 1, 1, 1, 1))))
    # Group events by day (makes table rendering logic simpler in template).
    event_list_by_days = list(itertools.imap(lambda x: list(x[1]),
        itertools.groupby(event_list, lambda e: (e['start_datetime'].year,
                                                 e['start_datetime'].month,
                                                 e['start_datetime'].day))
    ))
read_in_event_list()

# Automatically reread speakers.txt, schedule.txt and the files in 'abstracts/'.
if HAVE_WATCHDOG:
    class MyEventHandler(watchdog.events.FileSystemEventHandler):
        def __init__(self, action):
            self.action = action
            super(watchdog.events.FileSystemEventHandler, self).__init__()
        def on_modified(self, e):
            if not e.is_directory:
                filename = os.path.split(e.src_path)[1]
                self.action(filename)

    # Watch for changes to speakers.txt and schedule.txt
    ss_observer = watchdog.observers.Observer()
    ss_observer.schedule(MyEventHandler(lambda fname: {
                             'speakers.txt': read_in_speaker_list,
                             'schedule.txt': read_in_event_list
                         }.get(fname, lambda: ())()),
                         path=BASE,
                         recursive=False)
    ss_observer.start()

    # Watch for changes to abstracts.
    abs_observer = watchdog.observers.Observer()
    def abs_handler(fname):
        for s in speaker_list:
            if s['abstract_file'] == fname:
                abstract_title, abstract_html = read_in_abstract(fname)
                s['abstract_title'] = abstract_title
                s['abstract_html'] = abstract_html
                break
    abs_observer.schedule(MyEventHandler(abs_handler), path=os.path.join(BASE, 'abstracts'), recursive=False)

class Speakers(object):
    def GET(self):
        return render_wrapper('Speakers', render.speakers(speaker_list))

class Index(object):
    def GET(self):
        return render_wrapper('', render.index())

class Schedule(object):
    def GET(self):
        return render_wrapper('Schedule', render.schedule(event_list_by_days))

class Register(object):
    JS_EXTRAS = [conf.url_for('/static/register.js'), conf.url_for('/static/jquery.simplemodal.js')]

    def GET(self):
        if conf.__dict__.has_key('REGISTRATION_CLOSED') and conf.REGISTRATION_CLOSED:
            return render_wrapper('Register', render.register_closed())
        else:
            return render_wrapper('Register', render.register(), Register.JS_EXTRAS)

    def POST(self):
        if conf.__dict__.has_key('REGISTRATION_CLOSED') and conf.REGISTRATION_CLOSED:
            raise web.badrequest()

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
            raise web.internalerror()

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
