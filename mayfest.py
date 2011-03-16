import web

class Opts(object):
    """Wrap a dictionary so we can use the more concise foo.bar syntax to
       access options in templates. It's convenient to have __getattr__
       return the empty list as the default value for a key that isn't set,
       since this simplifies looping code in templates. The trade off is that
       we then need to special case display of the empty list as display of
       the empty string.
    """
    class ListWhereEmptyDisplaysAsEmptyString(list):
        def __init__(self, *args):
            super(list, self).__init__(*args)

        def __unicode__(self):
            if len(self) == 0:
                return u""
            else:
                raise Exception("Should not get here!")

        def __str__(self):
            raise Exception("NOT USING UNICODE!!!")

    def __init__(self, d):
       self.d = d

    def __getattr__(self, k):
        try:
            return self.d[k]
        except KeyError:
            return Opts.ListWhereEmptyDisplaysAsEmptyString()

    def update(self, opts):
        self.__dict__.update(opts.__dict__)

urls = (
    '/', 'index',
    '/schedule', 'schedule',
    '/speakers', 'speakers',
    '/register', 'register',
    '/directions', 'directions',
    '/accommodation', 'accommodation',
    '/main.css', 'maincss'
)

app = web.application(urls, globals())

tglobs = dict(int=int, str=str, url_for=lambda x: x, websafe=web.websafe)
render = web.template.render('templates/', globals=tglobs)

def render_wrapper(title, template, js_includes=[]):
    print "_______\n", web.ctx.env['HTTP_ACCEPT'], "\n\n"
    if web.ctx.env['HTTP_ACCEPT'].find('text/json') != -1:
        return template
    else:
        return render.wrapper(title, template, js_includes)

class index:
    def GET(self):
        return render_wrapper('', render.index())
class schedule:
    def GET(self):
        return render_wrapper('Schedule', render.schedule())

# Read speakers CSV db.
speakers_f = open("speakers.txt")
speaker_list = []
for l in speakers_f:
    l = l.rstrip('\n')
    fields = l.split(';')
    assert len(fields) == 4
    speaker_list.append(dict(name=fields[0], institution=fields[1], homepage=fields[2], abstractfile=fields[3]))
class speakers:
    def GET(self):
        return render_wrapper('Speakers', render.speakers(map(Opts, speaker_list)))

class register:
    def GET(self):
        return render_wrapper('Register', render.register(), [tglobs['url_for']('/static/register.js')])

    def POST(self):
        data = web.input(friday="no", saturday="no", reception="no", crash="no")
        for k in ('name', 'aff', 'email'):
            if not data.has_key(k):
                web.badrequest()

        f = None
        try:
            f = open("registrations", "a")
            def ersatz(s): return s.replace("%", "%25").replace("\n", "%0a")
            for k in ('name', 'aff', 'email', 'friday', 'saturday', 'reception', 'crash', 'comments'):
                f.write("%s: %s\n" % (k, data[k] if data.has_key(k) else ''))
            f.write('\n')
        except IOError, e:
            web.internalerror()
        finally:
            f.close()

        return render_wrapper('Register', render.register_success())

class directions:
    def GET(self):
        return render_wrapper('Directions', render.directions())

class accommodation:
    def GET(self):
        return render_wrapper('Accommodation', render.accommodation())

class maincss:
    def GET(self):
        return render.main()

if __name__ == "__main__": app.run()
