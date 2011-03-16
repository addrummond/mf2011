function verifyRegistration() {
    var valid = true;
    if (document.MayFestRegistration.name.value.match(/^\s*$$/)) {
        valid = false;
    }
    if (document.MayFestRegistration.email.value.match(/^\s*$$/)) {
        valid = false;
    }
    if (document.MayFestRegistration.aff.value.match(/^\s*$$/)) {
        valid = false;
    }
    // Here we decide whether to submit the form.
    if (! valid) {
        alert("Please make sure you enter your name, email address, and academic affiliation.")
    }
    return valid;
}