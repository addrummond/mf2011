history = window.history || (typeof(history) != "undefined" ? history : null);

var baseTime;

$(document).ready(function() {
    baseTime = new Date().getTime();

    if (history && history.pushState) {
        function handler (href, name) {
            return function (e) {
                e.stopPropagation();
                e.preventDefault();
                loadpage(href, name, true);
                return false;
            }
        }

        var navs = $("ul.nav li");
        for (var i = 0; i < navs.length; ++i) {
            var nav = $(navs[i]);
            var a = nav.find('a');
            nav.click(handler(a[0].href, a[0].innerHTML));
            a.click(handler(a[0].href, "Mayfest 2011 - " + a[0].innerHTML));
        }

        $(window).bind('popstate', function (e) {
            // Don't trigger on initial page load. This seems to be a bit buggy in FF,
            // so we also ensure that we're not reacting to history entries entered
            // before the page was loaded.
            if (e.originalEvent.state && e.originalEvent.state.time && e.originalEvent.state.time >= baseTime) {
                loadpage(location.pathname, document.title, false);
            }
        });
    }
});

function loadpage(url, name, pushState) {
    var alreadyError = false;
    $.ajax({
        url: url,
        data: { _ajax: 'yes' },
        dataType: 'html',
        success: function (html) {
            if (pushState) {
                history.pushState({ url: url, time: new Date().getTime() }, name, url);
            }
            $("#contents").fadeOut("normal", function () { $("#contents").html(html); $("#contents").fadeIn("normal"); });
        },
        error: function () {
            if (! alreadyError) {
                alreadyError = true;
                alert("There was an error loading the page.");
            }
        }
    });
}