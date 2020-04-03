/*
MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
Copyright (C)2020 Connected Places Catapult

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Contact: musicc-support@cp.catapult.org.uk
         https://cp.catapult.org.uk/case-studies/musicc/ 
*/
function showInformationToast(text, hideAfter = 5000) {
    text = prettyPrintJson(text);
    return $.toast({
        heading: 'Information',
        text: text,
        showHideTransition: 'slide',
        icon: 'info',
        hideAfter: hideAfter
    });
}

function showErrorToast(text, hideAfter = 10000) {
    text = prettyPrintJson(text);
    text = stripScripts(text);
    return $.toast({
        heading: 'Error',
        text: text,
        showHideTransition: 'fade',
        icon: 'error',
        hideAfter: hideAfter
    });
}

function showSuccessToast(text, hideAfter = 5000) {
    text = prettyPrintJson(text);
    return $.toast({
        heading: 'Success',
        text: text,
        showHideTransition: 'slide',
        icon: 'success',
        hideAfter: hideAfter
    });
}



function prettyPrintJson(obj) {
    if (typeof (obj) === "object") {
        obj = JSON.stringify(obj, null, 2);
        obj = obj.slice(1, -1).replace(/\\n/g, "<br>");
    }
    else {
        obj = obj.replace(/\n/g, "<br>");
    }
    return obj;
}

function showProgressToast(text) {
    // Create a random but known id that we can refer to to set the css
    // Must be somewhat unique so that we don't conflict with another progress bar
    let random_id_string = Math.random().toString(36).substring(2, 6)
    text += `<br><div id='progressbar_${random_id_string}'></div>`
    let toast = showInformationToast(text, false)
    let progressbar = $(`#progressbar_${random_id_string}`).progressbar({
        value: false
    });
    let progressbarValue = progressbar.find(".ui-progressbar-value");
    progressbarValue.css({
        "background": 'rgb(142, 120, 181)'
    });
    return toast
}