$(document).ready(function() {
    if (window.history && window.history.pushState) {
        var navs = $("ul.nav li");
        for (var i = 0; i < navs.length; ++i) {
            var nav = $(navs[i]);
            function handler (a) {
                var alreadyOnIt = false;
                return function (e) {
                    if (alreadyOnIt)
                        return;
                    alreadyOnIt = true;
                    if (e)
                        e.stopPropagation();
                    
                    var alreadyError = false;
                    $.ajax({
                        url: a.href,
                        type: 'GET',
                        data: { },
                        beforeSend: function (x) { x.setRequestHeader('Accept', 'text/json'); },
                        dataType: 'html',
                        success: function (html) {
                            window.history.pushState(a.href, a.innerHTML, a.href);
                            $("#contents").fadeOut("fast", function() { $(this).html(html); $(this).fadeIn("fast"); });
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
            }
            var a = nav.find('a');
            nav.click(handler(a[0]));
            a.click(handler(a[0]));
        }
    }
});