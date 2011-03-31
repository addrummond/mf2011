if (! history)
    history = window.history;

// See comment for $(window).bind below.
var baseTime;

$(document).ready(function() {
    baseTime = new Date().getTime();

    if (history && history.pushState) {
        function handler (href, name) {
            return function (e) {
                e.stopPropagation();
                e.preventDefault();
                loadpage({type:'GET', url: href}, name, true);
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
                loadpage({type: 'GET', url: location.pathname }, document.title, false);
            }
        });
    }
});

//
// This involves some slightly nasty polling when the server is slow.
// To make the loading feel responsive, we want to begin fading the page
// out as soon as the user clicks the button. But since JS does't have
// real threading, that means we can only be notified asynch'ly when
// the fade is finished -- and not when the ajax loading is finished.
// So, once the fade is finished, we check to see if the page has
// finished loading, and if so (the usual case) we fade it in immediately.
// Otherwise, we show an ajax spinner and poll every 100ms to check
// for completion of the loading (or an error). Since the polling only
// happens when loading is already slow, the possibility of an additional
// <=100ms delay shouldn't make things noticably worse.
//
function loadpage(request, name, pushState) {
    if (! request.data)
        request.data = { };
    request.data._ajax = 'yes';
    request.dataType = 'html';
    request.success = function (html) {
        if (pushState) {
            history.pushState({ url: request.url, time: new Date().getTime() }, name, request.url);
        }
        loadedHtml = html;
    };
    request.error = function () {
        if (! loadError) {
            loadError = true;
            $("<div>").html(
                "<p class='error'>There was an error loading the page.</p>" +
                "<p><span class='simplemodal-close'>&laquo; back</span></p>"
            ).modal({closeHTML: ""});
        }
    };

    var loadedHtml = null;
    var loadError = null;
    $.ajax(request);

    function displayHtml(html)
    {
        var m = html.match(/^([^\n]*)/);
        var title = m[1];
        var m2 = document.title.match(/^([^-]+)/);
        document.title = title.match(/^\s*$/) ? m2[1] : m2[1] + " - " + title;
        $("#contents").html(html.substr(title.length + 1)).fadeIn("normal");
    }

    var bottomHr = $("#contents + hr");
    var contactInfo = $(".contact");
    bottomHr.fadeOut("normal");
    contactInfo.fadeOut("normal");
    $("#contents").fadeOut("normal", function () {
        var timeoutId;
        function whileNotLoaded() {
            if (loadedHtml) {
                clearTimeout(timeoutId);
                displayHtml(loadedHtml);
            }
            else if (loadError) {
                clearTimeout(timeoutId);
                $("#contents").fadeIn("normal");
            }
        }
        if (loadedHtml) {
            displayHtml(loadedHtml);
            bottomHr.fadeIn("normal");
            contactInfo.fadeIn("normal");
        }
        else {
            $("#contents")
            .empty()
            .append(spinnerOn = $("<div>").addClass("loader"))
            .show();
            timeoutId = setInterval(whileNotLoaded, 100);
        }
    });
}
