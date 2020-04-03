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
function toggleColumn(reference) {
    var column = getColumnFromReference(reference);
    column.visible(!column.visible());
}

function enableColumn(reference) {
    var column = getColumnFromReference(reference);
    column.visible(true);
}

function disableColumn(reference) {
    var column = getColumnFromReference(reference);
    column.visible(false);
}

function getColumnFromReference(reference) {
    if (typeof reference === "string")
        reference = reference + ":name";
    return searchPage.dataTable.column(reference);
}

//Render a 'key' column using the corresponding value from the json field
function renderColumn(key) {
    return function (data, type, row) {
        var jsonObject = row.metadata[key];
        if (typeof jsonObject === "undefined")
            return "-";

        // If the json data only has a value attribute, don't display it like an attribute
        if (jsonObject.hasOwnProperty("@value") && Object.keys(jsonObject).length == 1)
            jsonObject = jsonObject["@value"];
        return syntaxHighlight(jsonObject);
    };
}

function initialiseDataTable(schema) {
    $.fn.DataTable.ext.errMode = "throw";

    // Start with the id column and the metadata column with syntax-highlighted rendering
    var fieldIndices = {};
    var columns = [{ title: `<favorite-star id="favourite"><span class="favorite-star-character">&#x2605;</span></favorite-star>`, data: "favourited" }, { title: "id", data: "id" }, { title: "metadata", data: "metadata" }];
    var columnDefs = [{
        "name": "favourited",
        "targets": 0,
        "visible": true,
        "width": "4%",
        "orderable": false,
        render: function (data) {
            let active = data === true ? "active" : "";
            return `<favorite-star id="favourite"><span class="favorite-star-character" ${active}>&#x2605;</span></favorite-star>`
        }
    },
    {
        "name": "id",
        "targets": 1,
        "visible": false
    },
    {
        "render": syntaxHighlight,
        "name": "metadata",
        "targets": 2,
        "visible": false
    }];


    // Add a column for each field and render it
    getAllTopLevelFields(schema["properties"]).forEach((key, index) => {
        fieldIndices[key] = index + 3;

        columns.push({ title: key });
        columnDefs.push({
            "render": renderColumn(key),
            "targets": index + 3,
            "name": key,
            "visible": false
        });
    });

    columnDefs.find(o => o.name === 'label').width = "50%"
    columnDefs.find(o => o.name === 'updateDateTime').orderSequence = ["desc", "asc"]
    columns.push({ title: "info" });
    columnDefs.push({
        "targets": -1,
        "data": null,
        "orderable": false,
        width: "5%",
        render: function (data, type, row, meta) {
            var additionalSymbols = ""
            if (row["comments"]) {
                additionalSymbols += `<div class="comments"><div class="ui-icon ui-icon-comment"></div>${row["comments"]}</div>`
            }
            if (row["broken"]) {
                additionalSymbols += `<div class="ui-icon ui-icon-alert"
                 title="This scenario may be broken"></div>`
            }
            return `<a class='ui-icon ui-icon-info' href='${location.pathname}#${row.id}'></a>${additionalSymbols}`
        }
    });

    searchPage.dataTable = $('#result-table').DataTable({
        data: [],
        columns: columns,
        "columnDefs": columnDefs,
        "scrollX": true,
        "searching": false,
        "scrollY": "calc(100vh - var(--header-height) - 220px)",
        "dom": 'rt<"bottom"iflp<"clear">>',
        "pagingType": "full_numbers",
        "pageLength": 25,
        "colReorder": true,
        "order": [[3, "asc"]],

        "deferLoading": 0,
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "/query",
            "data": getPaginatedData,
            "dataSrc": "results"
        }
    });

    searchPage.dataTable.on('click', 'a', (event) => { event.stopPropagation() });
    searchPage.dataTable.on('draw', () => { enableDatatableColumnExpansion("#result-table", formatExpandedJsonView) });
    $("#result-table_wrapper .dataTables_scrollHead").on('click', '.favorite-star-character', (event) => {
        if ($(event.currentTarget).attr("active") === "") {
            $(event.currentTarget).removeAttr("active");
        }
        else {
            $(event.currentTarget).attr("active", "");
        }
        reloadTable();
        event.stopPropagation();
    });

    $("#result-table").on('click', '.favorite-star-character', (e) => {
        var id = searchPage.dataTable.row($(e.currentTarget).parents("tr")).data().uid
        var star = $(e.currentTarget)
        if (star.attr("active") !== "") {
            $.ajax({
                "url": "search/detail/tag/add", "data": { "id": id, "tag": "favourite" }, "success": () => {
                    star.attr("active", "");
                }
            });
        }
        else {
            $.ajax({
                "url": "search/detail/tag/remove", "data": { "id": id, "tag": "favourite" }, "success": () => {
                    star.removeAttr("active");
                }
            });
        }
        e.stopPropagation();
    })
        .on("preXhr.dt", (event) => {
            showInformationToast("Loading scenarios");

            // Start a timer
            var queryStartTime = +new Date();

            // Attach the event handler to process the next xhr event
            searchPage.dataTable.one('xhr', function (e, settings, resultSet, xhr) {
                processResultSet(resultSet, queryStartTime, xhr);
            });
        });
    $("#result-table").on('click', '.comments', (e) => {
        var infoButton = $(e.currentTarget).siblings(".ui-icon-info")[0]
        $("#detail-view").one("detail:load", () => {
            openTabByTarget("discussion-tab");
        });
        infoButton.click();

        e.stopPropagation();
    });


    enableDatatableColumnExpansion("#result-table", formatExpandedJsonView);

}

function moveColumnToPosition(title, index) {
    searchPage.dataTable.colReorder.move(getColumnFromReference(title)[0][0], index);
}

function getPaginatedData(searchData) {
    let newSearchData = undefined
    if (searchPage.dataTable && searchPage.dataTable.hasOwnProperty("queryString")) {

        var query = searchPage.dataTable.queryString || ""
        query = query.trim()

        var favouritesOnly = $("#result-table_wrapper .favorite-star-character").attr("active") === ""
        if (favouritesOnly) {
            if (query === "" || query === "*") {
                query = "Tags__Tag INCLUDES 'favourite'"
            }
            else {
                query = `(${query}) AND Tags__Tag INCLUDES 'favourite'`
            }
        }

        newSearchData = {
            page_length: searchData.length,
            page_number: (searchData.start + searchData.length) / searchData.length,
            query: query,
            order_column: searchData.columns[searchData.order[0].column].name
        }

        if (newSearchData.order_column !== "id" && newSearchData.order_column !== "metadata") {
            newSearchData.order_column = "metadata__" + newSearchData.order_column
        }
        newSearchData.order_direction = searchData.order[0].dir
        newSearchData.musicc_revision = $("#revision-selector").val()
    }
    return newSearchData
}

function formatExpandedJsonView(dataSet) {
    var formattedJson = $("<div>");
    formattedJson.jsonTable(dataSet.metadata, {
        arrayIndex: false
    });
    return formattedJson;
}

function reloadTable() {
    performQuery(searchPage.dataTable.queryString);
}

function performQuery(queryString) {



    // Set the queryString parameter of the datatable
    searchPage.dataTable.queryString = queryString
    // Force a reload of the table's data
    searchPage.dataTable.draw();
}


function processResultSet(resultSet, queryStartTime, xhr) {
    if (resultSet === null) {
        showErrorToast(xhr.statusText + ": " + xhr.responseText);
    }
    else {
        let timeTaken = new Date() - queryStartTime;
        var fileSizeString = ""

        if (resultSet.recordsFiltered > 0) {
            fileSizeString = "Estimated file size is: " + getReadableFileSizeString(resultSet.estimatedDownloadSize + resultSet.estimatedResourcesSize + resultSet.estimatedImagesSize);
            fileSizeString += "\nXML files - " + getReadableFileSizeString(resultSet.estimatedDownloadSize);
            fileSizeString += "\nResource files - " + getReadableFileSizeString(resultSet.estimatedResourcesSize);
            fileSizeString += "\nImage files - " + getReadableFileSizeString(resultSet.estimatedImagesSize);
            $(searchPage.dataTable.containers()[0]).trigger("search:success", [resultSet, fileSizeString]);
        }
        else {
            $(searchPage.dataTable.containers()[0]).trigger("search:failure");
        }

        showSuccessToast("Query returned " + resultSet.recordsFiltered + " results in " + timeTaken + "ms" +
            "\n" + fileSizeString);
    }
}
