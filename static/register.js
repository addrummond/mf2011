$(document).ready(function() {
    $("#register").submit(function () {
        if (! verifyRegistration($("#register")[0])) {
            $("<div>").html(
                "<p class='error'>The form was not completed.</p>" +
                "<p>Please make sure you enter your name, email address, and academic affiliation.</p>" +
                "<p><span class='simplemodal-close'>&laquo;back to form</span></p>").modal({
                closeHTML: ""
            });
            return false;
        }
        else return true;
    });
});

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