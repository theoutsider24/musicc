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
$(document).ready(function () {
    $("#tabs").tabs();
    attachAjaxLogoutInterceptor();

    $("form#zip_file_upload_form").on('submit', function (event) {
        $.ajax({
            type: this.method,
            url: this.action,
            data: new FormData(this),
            cache: false,
            contentType: false,
            processData: false,

            success: (val) => {
                if (typeof (val) === "object" && val.hasOwnProperty("errors") && !$.isEmptyObject(val.errors)) {
                    showErrorToast(val.errors, false);
                }
                else {
                    showSuccessToast(val);
                }

                var validate_only_checkbox = $(this).serializeArray().filter((val) => val.name === "validate_only")[0]
                var validate_only = (validate_only_checkbox ? validate_only_checkbox.value : "false") === "true";
                if (!validate_only) {
                    this.reset();
                    submissionsTable.ajax.reload();
                    $("#submission-form").dialog("close");
                }
            },
            failure: (val) => {
                showErrorToast(val, false);
            },
            error: (val) => {
                showErrorToast(val.responseText, false);
            },
        });
        event.preventDefault();
    });
    initialiseSubmissionsTab();
    initialiseRegisteredSystemsTab();
    $("#submission-form").dialog({
        autoOpen: false,
        height: 400,
        width: 350,
        modal: true,
        buttons: {
            "Submit": function () {
                $("#submission-form").find("form").submit()
            },
            Cancel: function () {
                $("#submission-form").dialog("close");
                $("#submission-form").find("form")[0].reset();
            }
        },
        close: function () {
            $("#submission-form").dialog("close");
            $("#submission-form").find("form")[0].reset();
        }
    });
    $("#submission-form-open").click(() => { $("#submission-form").dialog("open") });
    $(window).resize(function () {
        $("#submission-form").dialog("option", "position", { my: "center", at: "center", of: window });
    });
});

function initialiseSubmissionsTab() {
    initialiseSubmissionsTable();
}
var submissionsTable;
function initialiseSubmissionsTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "Change ID", data: "id" },
        { title: "Changes" },
        { title: "Submission Time", data: "updated_date_time" },
        { title: "Reviewer", data: "reviewed_by" },
        { title: "MUSICC Revision", data: "musicc_revision" },
        { title: "Submission Status", data: "status" }
    ];

    submissionsTable = $('#submissions-table').DataTable({
        data: [],
        columns: columns,
        columnDefs: [
            {
                "targets": 1,
                "render": (data, type, row) => {
                    return `<button class='diff'>View diff</button>`
                }
            }],
        "order": [[0, "desc"]],
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/curation/submissions_queue",
        }
    });

    submissionsTable.on('click', 'button.diff', function (e) {
        var changeId = submissionsTable.row($(e.currentTarget).parents('tr')).data()["id"]
        displayModalChangeDiff(changeId)
        e.stopPropagation();
    });

    submissionsTable.on('draw', () => { enableDatatableColumnExpansion("#submissions-table", renderChangeSummary) });
}

function displayModalChangeDiff(change_id) {
    $.ajax({
        "url": "/search/detail/diff/change",
        "data": {
            id: change_id
        }
    }).done((data) => {
        if (data) {
            var modalContainer = $("<div>")
            data.diffs.forEach((diff) => {
                var container = $("<div>").addClass("modal-diff")
                //Remove second line which is blank but shouldn't be
                var lines = diff.split('\n');
                lines.splice(1, 1);
                var newDiff = lines.join('\n');

                var diffHtml = Diff2Html.getPrettyHtml(newDiff,
                    { inputFormat: 'diff', showFiles: false, matching: 'lines', outputFormat: 'line-by-line' }
                );

                container.html(diffHtml);
                modalContainer.append(container)
            });

            modalContainer.dialog({
                resizable: false,
                height: window.innerHeight - 100,
                width: "calc(100% - 50px)",
                modal: true,
                closeOnEscape: false,
                draggable: false,
            });
        }
    });
}

