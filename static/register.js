function regHandler() {
    if (! verifyRegistration($("#register")[0])) {
        $("<div>").html(
            "<p class='error'>The form was not completed.</p>" +
            "<p>Please make sure you enter your name, email address, and academic affiliation.</p>" +
            "<p><span class='simplemodal-close'>&laquo;back to form</span></p>"
        ).modal({closeHTML: ""});
        return false;
    }
    else {
        var data = { ajax: "yes" };
        var inps = $("#register input");
        for (var i = 0; i < inps.length; ++i) {
            var inp = $(inps[i]);
            if (inp.attr('type') == "text")
                data[inp.attr('name')] = inp.val();
            else if (inp.attr('type') == "checkbox" && inp.attr('checked'))
                data[inp.attr('name')] = inp.attr('checked');
        }
        var tas = $("#register textarea");
        for (var i = 0; i < tas.length; ++i) {
            var ta = $(tas[i]);
            data[ta.attr('name')] = ta.val();
        }
        loadpage({type: 'POST', url: BASE_URI + '/register', data: data }, null, false/*no need because URL doesn't change.*/);
        
        return false;
    }
}

function verifyRegistration(form) {
    var valid = true;
    if ($(form).find('input[name=name]').val().match(/^\s*$$/)) {
        valid = false;
    }
    if ($(form).find('input[name=email]').val().match(/^\s*$$/)) {
        valid = false;
    }
    if ($(form).find('input[name=aff]').val().match(/^\s*$$/)) {
        valid = false;
    }
    return valid;
}
