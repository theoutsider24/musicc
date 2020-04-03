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
function disableEnterButton(selector) {
    $(selector).off("keypress").keypress(
        function (event) {
            if (event.which === 13) {
                event.preventDefault();
            }
        });
}

function enableEnterButton(selector, func) {
    $(selector).off("keypress").keypress(
        function (event) {
            if (event.which === 13) {
                func(event);
            }
        });
}

function getReadableFileSizeString(fileSizeInBytes) {
    var i = -1;
    var byteUnits = [' kB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];
    do {
        fileSizeInBytes = fileSizeInBytes / 1024;
        i++;
    } while (fileSizeInBytes > 1024);

    return Math.max(fileSizeInBytes, 0.1).toFixed(1) + byteUnits[i];
}


function attachAjaxLogoutInterceptor() {
    // This function allows for redirecting to the login screen if one of our AJAX requests comes back with a login poge redirect
    var _oldAjax = $.ajax;
    $.ajax = function (options) {
        var _oldComplete = options.hasOwnProperty("complete") ? options.complete : () => { };
        var _oldError = options.hasOwnProperty("error") ? options.error : () => { };

        function detectRedirect(response) {
            // If an ajax call returns the login page html, redirect to the login page
            if ((!response.responseText && response.status !== 500 && response.getResponseHeader("content-type").includes("text/html"))
                || (response.responseText && response.responseText.includes("You are not logged in"))) {
                window.location.replace(window.location.origin + "/accounts/login/?next=" + window.location.pathname)
            }
        }

        var complete = function (response, status) {
            detectRedirect(response);
            _oldComplete(response, status);
        }

        var error = function (response, status) {
            detectRedirect(response);
            _oldError(response, status);
        }

        $.extend(options, {
            complete: complete,
            error: error
        });
        return _oldAjax(options);
    };
}

function submitDownloadForm(e) {
    e.data.extraData = e.data.extraData ? `&${e.data.extraData}` : ""
    e.preventDefault();
    let inProgressToast = showProgressToast("Preparing download");
    $.ajax({
        url: e.data.url,
        type: 'get',
        data: $(e.currentTarget).serialize() + e.data.extraData,
        xhrFields: {
            responseType: 'blob'
        },
        success: function (data, status, xhr) {
            // Exit if we expected a file but got html
            if (!xhr.getResponseHeader("content-type").includes("text/html")) {

                // Get the filename from the header's content-disposition
                var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                var matches = filenameRegex.exec(xhr.getResponseHeader("content-disposition"));
                var filename = ""
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }

                if (window.navigator && window.navigator.msSaveOrOpenBlob) {
                    // for IE and Edge
                    window.navigator.msSaveOrOpenBlob(data, filename);
                }
                else {
                    // Create and trigger a download link based on the data received
                    var a = document.createElement('a');
                    var url = window.URL.createObjectURL(data);
                    a.href = url;
                    a.download = filename;

                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }
            }
            inProgressToast.close();
        },
        error: function (response) {
            showErrorToast(`Download failed - ${response.statusText}`)
            inProgressToast.close();
        }
    });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function stripScripts(s) {
    var div = document.createElement('div');
    div.innerHTML = s;
    var scripts = div.getElementsByTagName('script');
    var i = scripts.length;
    while (i--) {
        scripts[i].parentNode.removeChild(scripts[i]);
    }
    return div.innerHTML;
}



function enableDatatableColumnExpansion(selector, formatFunction) {
    $(selector).off('click', 'tbody tr.odd, tbody tr.even').on('click', 'tbody tr.odd, tbody tr.even', function (event) {
        var tr = $(this);
        var row = $(event.delegateTarget).DataTable().row(tr);

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            row.child(formatFunction(row.data())).show();
            tr.addClass('shown');
        }
    });
}

function renderChangeSummary(dataSet) {
    var formattedJson = $("<div>");

    $.ajax({ "url": "/curation/change_log/summary", "data": { "id": dataSet.id } }).done((data) => {
        var jsonViewer = new JSONViewer();
        formattedJson.append(jsonViewer.getContainer());
        jsonViewer.showJSON(data.data);

        if (dataSet.type === "CREATE" && !dataSet.revertedBy) {
            var musiccRows = formattedJson.find("a.list-link:contains('Musicc')").siblings("ul").find("li span")
            musiccRows.each((i, el) => {
                var link = $("<a class='type-string'>")
                var element = $(el);
                var text = element.text();
                var idAnchor = text.substring(1, text.indexOf(" "));
                link.attr("href", `${location.pathname}${idAnchor}`).text(text);
                element.replaceWith(link)
            });
        }

    });

    return formattedJson;
}