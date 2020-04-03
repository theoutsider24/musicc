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
function initialiseChangesTab() {
    initialiseChangesTable();
}
var changesTable;
function initialiseChangesTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "Change ID", data: "id" },
        { title: "Change Type", data: "type" },
        { title: "Revert Change", data: "revertedBy" },
        { title: "Time", data: "updated_date_time" },
        { title: "User", data: "updated_by_user" },
        { title: "MUSICC Revision", data: "musicc_revision" }
    ];

    changesTable = $('#changes-table').DataTable({
        data: [],
        columns: columns,
        columnDefs: [{
            "targets": 2,
            "data": null,
            "render": (data) => data ? `Reverted by: ${data}` : `<button class='revert'>Revert</button>`
        }],
        "order": [[0, "desc"]],
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/curation/change_log",
        }
    });

    changesTable.on('draw.dt', function () {
        let table = this;
        let rows = $(table).find("tbody > tr");
        rows.each((i, el) => {
            if ($(el).find("td:nth-child(3)").text() !== "Revert")
                $(el).addClass("reverted");
            else {
                if ($(el).find("td:nth-child(2)").text() === "CREATE")
                    $(el).addClass("creation");
                else if ($(el).find("td:nth-child(2)").text() === "DELETE")
                    $(el).addClass("deletion");
            }
        });
    });

    changesTable.one('draw.dt', function () {
        let table = this;
        $(table).on('click', 'button.revert', function (event) {
            var changeId = changesTable.row($(this).parents('tr')).data()["id"]

            showConfirmationDialog("Confirm reversion", "Are you sure you want to revert change " + changeId + "?", function () {
                $.ajax({
                    url: "/revert",
                    type: "get",
                    data: {
                        id: changeId,
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

            event.stopPropagation();
        });

    });

    changesTable.on('draw', () => { enableDatatableColumnExpansion("#changes-table", renderChangeSummary) });
}
