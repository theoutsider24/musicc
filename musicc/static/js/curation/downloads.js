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
function initialiseDownloadsTab() {
    initialiseDownloadsTable();
}

var downloadsTable
function initialiseDownloadsTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "", data: "" },
        { title: "Download ID", data: "id" },
        { title: "Download type", data: "type" },
        { title: "Concrete per logical", data: "concrete_per_logical" },
        { title: "Query", data: "query" },
        { title: "Time", data: "date" },
        { title: "User", data: "user" },
        { title: "MUSICC Revision", data: "musicc_revision" }
    ];

    downloadsTable = $('#downloads-table').DataTable({
        data: [],
        columnDefs: [{
            "name": "",
            "targets": 0,
            "orderable": false,
            "render": (data, type, row) => {
                var is_native = (row.type === "NATIVE");

                return `<button class="download">Download</button>
                <form class="download">
                    <input type="hidden" name="query_id" value="` + row.query_id + `">
                    <input type="hidden" name="native" value="` + is_native + `">
                    <input type="hidden" name="previous_download_id" value="` + row.id + `">
                </form>`
            }
        }],
        columns: columns,
        "order": [[1, "desc"]],
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/curation/download_log",
        }
    });

    downloadsTable.one("draw", () => {
        $("#downloads-table.display")
            .on('submit', 'form', { url: '/download' }, submitDownloadForm)
            .on('click', 'button.download', event => {
                event.stopPropagation();
                $(event.currentTarget).next("form").submit();
            });
    });

    downloadsTable.on('draw', () => { enableDatatableColumnExpansion("#downloads-table", renderDownloadSummary) });
}

function renderDownloadSummary(dataSet) {
    var formattedJson = $("<div>");

    $.ajax({ "url": "/curation/download_log/summary", "data": { "id": dataSet.id } }).done((data) => {
        var jsonViewer = new JSONViewer();
        formattedJson.append(jsonViewer.getContainer());
        jsonViewer.showJSON(data.data);
    });

    return formattedJson;
}