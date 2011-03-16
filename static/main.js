history = window.history || (typeof(history) != "undefined" ? history : null);

function loadpage(url, name) {
    return; // Not working atm.
    var alreadyError = false;
    $.ajax({
        url: url,
        data: { _ajax: 'yes' },
        dataType: 'html',
        success: function (html) {
            history.pushState({ previous_url: window.location + '', previous_title: document.title + '' }, name, url);
            $(this).html(html);
        },
        error: function () {
            if (! alreadyError) {
                alreadyError = true;
                alert("There was an error loading the page.");
            }
        }
    });
    
    return false;
}

$(document).ready(function() {
    if (history && history.pushState) {
        function handler (href, name) {
            return function (e) {
                if (e)
                    e.stopPropagation();
                loadpage(href, name);
            }
        }

        var navs = $("ul.nav li");
        for (var i = 0; i < navs.length; ++i) {
            var nav = $(navs[i]);
            var a = nav.find('a');
            nav.click(handler(a[0].href, a[0].innerHTML));
            a.click(handler(a[0].href, "Mayfest 2011 - " + a[0].innerHTML));
        }

        window.onpopstate = function (e) {
            if (e.state) {
                loadpage(e.state.previous_url, e.state.previous_title);
                return false;
            }
        }
    }
});