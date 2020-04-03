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
function initialiseApprovalsTab() {
    initialiseApprovalsTable();
}
var approvalsTable;
function initialiseApprovalsTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "Change ID", data: "id" },
        { title: "Change Type", data: "type" },
        { title: "Submission Time", data: "updated_date_time" },
        { title: "Submitted by", data: "submitted_by" },
        { title: "MUSICC Revision", data: "musicc_revision" },
        { title: "Submission Status", data: "status" }
    ];

    approvalsTable = $('#approvals-table').DataTable({
        data: [],
        columns: columns,
        columnDefs: [{
            "targets": -1,
            "data": null,
            "defaultContent": `<button class='approve' action='approve'>Approve</button>
            <button class='reject' action='reject'>Reject</button>`
        },
        {
            "targets": 1,
            "render": (data, type, row) => {
                if (data === "CREATE") {
                    return `CREATE <button class='diff'>View diff</button>
                    <button class='download'>Download scenarios</button>
                    <form class="download">
                        <input type="hidden" name="id" value="${row.id}">
                    </form>
                    `
                }
            }
        }],
        "order": [[0, "desc"]],
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/curation/approval_queue",
        }
    });

    approvalsTable.on('click', 'button.approve, button.reject', function (e) {
        var requestId = approvalsTable.row($(e.currentTarget).parents('tr')).data()["request_id"]
        var changeId = approvalsTable.row($(e.currentTarget).parents('tr')).data()["id"]
        var action = $(e.currentTarget).attr("action")
        showConfirmationDialog("Confirm approval", `Are you sure you want to ${action} change ${changeId}?`, function () {
            $.ajax({
                url: `/curation/${action}`,
                type: "get",
                data: {
                    id: requestId,
                },
                success: (val) => {
                    showSuccessToast(val);
                    refreshTables()
                },
                failure: (val) => {
                    showErrorToast(val);
                },
                error: (val) => {
                    showErrorToast(val.responseText);
                },
            });
        });

        e.stopPropagation();
    })
        .on('click', 'button.diff', function (e) {
            var changeId = approvalsTable.row($(e.currentTarget).parents('tr')).data()["id"]
            displayModalChangeDiff(changeId)
            e.stopPropagation();
        })
        .on('submit', 'form.download', { url: 'curation/download_change' }, submitDownloadForm)
        .on('click', 'button.download', event => {
            event.stopPropagation();
            $(event.currentTarget).next("form").submit();
        });

    approvalsTable.on('draw', () => { enableDatatableColumnExpansion("#approvals-table", renderChangeSummary) });
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