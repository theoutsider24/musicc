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
var revisionTable
var searchPage = {}
var revisions = []
$(document).ready(function () {
    $("#tabs").tabs();
    attachAjaxLogoutInterceptor();
    createRevisionUploadForm();



    $("#revision-selector").on("change", () => {
        if (getSelectedRevision())
            loadRevision(getSelectedRevision());
    });
    initaliseRevisionTable().on("draw", () => {
        var data = revisionTable.rows().data();
        $("#revision-selector").empty();

        var newRevisions = [];
        data.each(function (value, index) {
            newRevisions.push(value.mus_rev);
            $("#revision-selector").append($("<option>").text(value.mus_rev));
        });


        if (!searchPage.dataTable || !searchPage.dataTable.ajax.params().musicc_revision) {
            // First time rendering the result table
            $("#revision-selector").val(newRevisions[0]).trigger("change");
        }
        else {
            if (!revisions.includes(newRevisions[0]))
                $("#revision-selector").val(newRevisions[0]).trigger("change");
            else
                $("#revision-selector").val(searchPage.dataTable.ajax.params().musicc_revision)
        }
        revisions = newRevisions;
    });

    initialiseChangesTab();
    initialiseApprovalsTab();
    initialiseDownloadsTab();

    $(".ui-tabs-tab a").on("click", (e) => {
        $($(e.currentTarget).attr("href")).find(".dataTables_scrollBody table").DataTable().columns.adjust()
    });
});

function getSelectedRevision() {
    return $("#revision-selector").val()
}
function refreshTables() {
    loadRevision(searchPage.dataTable.ajax.params().musicc_revision);
    revisionTable.ajax.reload();
    changesTable.ajax.reload();
    approvalsTable.ajax.reload();
}

function submitDeletions() {
    var revision = searchPage.dataTable.ajax.params().musicc_revision
    var queryString = "";
    $("tr").has("td:nth-child(1) input:checked").find("td:nth-child(4)").each(function () {
        queryString += " OR label = '" + $(this).text() + "'";
    });
    queryString = queryString.substr(4);

    $.ajax({ "url": "/query", "data": { "query": queryString, "musicc_revision": revision } })
        .done((data) => {
            if (data.recordsFiltered > 0) {
                var scenarioList = $("<ul>");
                data.results.forEach(element => {
                    scenarioList.append($("<li>").text(element.metadata.label))
                });

                var confirmationDialogContent = $("<div>")
                    .append(
                        $("<span>")
                            .text("These are the scenarios which will be deleted")
                    )
                    .append(
                        $("<p>")
                            .text("All versions of these scenarios within the current revision (" + revision + ") will be deleted")
                    )
                    .append(scenarioList)
                showConfirmationDialog("Confirm deletion", confirmationDialogContent, function () {
                    $.ajax({ "url": "/delete", "data": { "query_string": queryString, "revision": revision } })
                        .done(() => {
                            showSuccessToast("Records deleted")
                            refreshTables();
                        });
                    showInformationToast("Processing deletion");
                });
            }
        });

    return queryString
}

function showConfirmationDialog(title, content, targetFunction) {
    $("#dialog-confirm > p").children().not(".ui-icon").remove();

    if (typeof (content) === "string") {
        content = $("<span>").text(content);
    }

    $("#dialog-confirm")
        .attr("title", title)
        .find("p")
        .append(
            content
        )

    $("#dialog-confirm").dialog({
        resizable: false,
        height: "auto",
        width: 400,
        modal: true,
        closeOnEscape: true,
        buttons: {
            "Confirm": function () {
                targetFunction();
                $(this).dialog("close");
            },
            Cancel: function () {
                $(this).dialog("close");
            }
        }
    });
}

function initialiseScenarioTable(schema) {
    $.fn.DataTable.ext.errMode = "throw";

    // Start with the id column and the metadata column with syntax-highlighted rendering
    var fieldIndices = {};
    var columns = [{ title: "Select" }, { title: "Edit" }, { title: "Scenario ID", data: "id" }, { title: "metadata", data: "metadata" }];
    var columnDefs = [{
        "name": "select",
        "targets": 0,
        "render": () => {
            return `<input type="checkbox"></input>`
        }
    },
    {
        "name": "edit",
        "targets": 1,
        "render": () => {
            return `<button class="edit ui-icon ui-icon-pencil"></button>`
        }
    },
    {
        "name": "id",
        "targets": 2
    },
    {
        "render": syntaxHighlight,
        "name": "metadata",
        "targets": 3,
        "visible": false
    }];


    // Add a column for each field and render it
    getAllTopLevelFields(schema["properties"]).forEach((key, index) => {
        fieldIndices[key] = index + 4;

        columns.push({ title: key });
        columnDefs.push({
            "render": renderColumn(key),
            "targets": index + 4,
            "name": key,
            "visible": false
        });
    });

    searchPage.dataTable = $('#result-table').DataTable({
        data: [],
        columns: columns,
        "columnDefs": columnDefs,
        "scrollX": true,
        "searching": false,
        "scrollY": "calc(100vh - var(--header-height) - 220px)", //change this
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "paging": false,
        "colReorder": true,

        "deferLoading": 0,
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "/query",
            "data": getPaginatedData,
            "dataSrc": "results"
        }
    });

    searchPage.dataTable.on('draw', () => { enableDatatableColumnExpansion("#result-table", formatExpandedJsonView) });
    searchPage.dataTable.on('draw', resetDeleteButton);
    searchPage.dataTable.one("draw", () => {
        $("#result-table.display")
            .on('click', 'input[type=checkbox]', event => {
                event.stopPropagation();
                resetDeleteButton();
            });
        $("#result-table.display")
            .on('click', 'button.edit', event => {
                event.stopPropagation();
                createEditorPopup(event);
            });
    })
    searchPage.dataTable.on('preDraw', () => {
        var selectedLabels = saveSelections();
        searchPage.dataTable.one("draw", () => { applySavedSelections(selectedLabels) });
    });
    enableColumn("label")
    enableColumn("updateDateTime")
    enableColumn("updateUsername")
    enableColumn("version")


    $('#result-table_wrapper .toolbar').append($("<button>").text("Select all").attr("id", "select-all").click(selectAllScenarios));
    $('#result-table_wrapper .toolbar').append($("<button>").text("Delete selected").attr("id", "delete").attr("disabled", "disabled").click(submitDeletions));
}

function resetDeleteButton() {
    if ($("#result-table input:checkbox:checked").length) {
        $("#result-table_wrapper #delete").removeAttr("disabled");
    }
    else {
        $("#result-table_wrapper #delete").attr("disabled", "disabled");
    }
}


var musiccSchema = undefined
function loadRevision(revision) {
    $.ajax({ "url": "/get_metadata_fields", "data": { "revision": revision } })
        .done((schema) => {
            musiccSchema = schema;
            $("#result-table_wrapper").replaceWith('<table id="result-table" class="display" style="width:100%">');

            initialiseScenarioTable(schema);
            performQuery("");
        });
}


function initaliseRevisionTable() {
    var csrftoken = getCookie('csrftoken');
    $.fn.DataTable.ext.errMode = 'throw';
    revisionTable = $("#revision-table").DataTable({
        "searching": false,
        "paging": false,
        "ordering": false,
        "info": false,
        "sDom": '<"toolbar">t',
        "ajax": {
            "url": "/get_revision_info",
            "dataSrc": "results"
        },
        "columns": [
            { "data": "mus_rev" },
            { "data": "odr_rev" },
            { "data": "osc_rev" },
            { "data": "start_date" },
            { "data": "scenario_count" }
        ],
        "columnDefs": [{
            "targets": 3,
            "data": null,
            "defaultContent": "<button class='activate'>Activate</button>"
        },
        {
            "targets": 5,
            "data": null,
            render: function (data, type, row, meta) {
                return `<div id="zip_file_upload">
                    <form method="post" enctype="multipart/form-data" action="/upload_zip">
                        <input type="file" name="file_ingestion_zip" accept=".zip" hidden>
                        <input type="hidden" name="revision" value="` + row["mus_rev"] + `">
                        <input type="hidden" name="csrfmiddlewaretoken" value="` + csrftoken + `">
                        <button type="submit" class="submit">Upload</button>
                    </form>
                </div>`
            }
        },
        {
            "targets": 6,
            "data": null,
            render: function (data, type, row, meta) {
                return `<form class="download dump-scenarios" method="get">
                            <input type="hidden" name="revision" value="` + row["mus_rev"] + `">
                            <input type="hidden" name="csrfmiddlewaretoken" value="` + csrftoken + `">
                            <button type="submit" class="submit">Dump Scenarios</button>
                        </form>
                        <form class="download dump-schema" method="get">
                            <input type="hidden" name="revision" value="` + row["mus_rev"] + `">
                            <input type="hidden" name="csrfmiddlewaretoken" value="` + csrftoken + `">
                            <button type="submit" class="submit">Dump Schema</button>
                        </form>`
            }
        }]
    });

    $('#revision-table_wrapper .toolbar').append($("<button>").text("Add a new revision").click(openRevisionUploadForm));

    revisionTable.on('click', 'button.activate', function () {
        var revisionNumber = revisionTable.row($(this).parents('tr')).data()["mus_rev"]
        $.ajax({
            url: "/activate_revision",
            type: "get",
            data: {
                revision: revisionNumber,
            },
            success: (val) => {
                showSuccessToast(val);
                refreshTables();
            },
            failure: (val) => {
                showErrorToast(val);
            },
            error: (val) => {
                showErrorToast(val.responseText);
            },
        });
    });

    revisionTable.on('draw.dt', function () {
        let table = this;
        let rows = $(table).find("tbody > tr");
        rows.each((i, el) => {
            if ($(el).find("td:nth-child(4)").text() !== "Activate")
                $(el).addClass("active");
            else
                $(el).addClass("inactive");
        });

        regisisterFormSubmitHandlers();
    });

    regisisterFormSubmitHandlers();
    return revisionTable;
}

function regisisterFormSubmitHandlers() {
    $("form:not(.download)").off('submit').on('submit', function (event) {
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
                refreshTables();
                this.reset();
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

    $(".dump-scenarios, .dump-scenarios").off('submit');
    $(".dump-scenarios").submit({ url: '/dump/musicc' }, submitDownloadForm);
    $(".dump-schema").submit({ url: '/dump/schema' }, submitDownloadForm);
}

function createEditorPopup(event) {
    var id = searchPage.dataTable.row($(event.currentTarget).parents('tr')).data()["uid"]

    $.ajax({ url: "/curation/editable_musicc", data: { "id": id } }).done(data => {
        var editor = $("<textarea wrap='off'>").text(data);
        $("body").append(editor);
        editor.dialog({
            height: 500,
            width: 550,
            modal: true,
            buttons: {
                Submit: function () {
                    validateEditorContent(editor, id, function () {
                        $.post({
                            url: "/curation/editable_musicc/submit",
                            data: {
                                id: id,
                                content: editor.val(),
                                csrfmiddlewaretoken: getCookie("csrftoken")
                            },
                            success: function (data) {
                                showSuccessToast(data);
                                refreshTables();

                                editor.dialog("destroy");
                                editor.remove();
                            },
                            error: function (response, status, error) {
                                showErrorToast(response.responseText);
                            }
                        });
                    });
                },
                Validate: () => { validateEditorContent(editor, id) },
                Cancel: function () {
                    $(this).dialog("destroy");
                    $(this).remove();
                }
            },
            close: function () {
                $(this).dialog("destroy");
                $(this).remove();
            }
        });
        editor.on("input", (event) => {
            editor.removeClass("invalid").removeClass("valid");
        });
        editor.css("width", "100%");

        $("<div>").addClass("toast-container").appendTo(editor.parent(".ui-dialog"))
    });
}

function createRevisionUploadForm() {
    getRevisionUploadForm().dialog({
        autoOpen: false,
        height: 400,
        width: 350,
        modal: true,
        buttons: {
            "Create Revision": function () {
                getRevisionUploadForm().find("form").submit()
            },
            Cancel: function () {
                closeRevisionUploadForm();
                resetRevisionUploadForm();
            }
        },
        close: function () {
            closeRevisionUploadForm();
            resetRevisionUploadForm();
        }
    })
}

function openRevisionUploadForm() {
    getRevisionUploadForm().dialog("open");
}

function closeRevisionUploadForm() {
    getRevisionUploadForm().dialog("close");
}

function resetRevisionUploadForm() {
    getRevisionUploadForm().find("form")[0].reset();
}

function getRevisionUploadForm() {
    return $("#revision-file-upload");
}

function selectAllScenarios() {
    if ($("#result-table input:checkbox:not(:checked)").length) {
        $("#result-table input:checkbox:not(:checked)").click();
    }
    else {
        $("#result-table input:checkbox").click();
    }
}

function saveSelections() {
    var labels = []
    $("tr").has("td:nth-child(1) input:checked").find("td:nth-child(4)").each(function () {
        labels.push($(this).text())
    });
    return labels
}

function applySavedSelections(labels) {
    labels.forEach(label => {
        $("td").filter(function () {
            return $(this).text() === label
        }).parent("tr").find("input:checkbox").prop('checked', true);
    });
    resetDeleteButton();
}

function validateEditorContent(editor, id, success = () => { }) {
    $.post({
        url: "/curation/editable_musicc/validate",
        data: {
            id: id,
            content: editor.val(),
            csrfmiddlewaretoken: getCookie("csrftoken")
        },
        success: function (data) {
            editor.addClass("valid").removeClass("invalid");
            $(".toast-container").empty();
            success();
        },
        error: function (response, status, error) {
            editor.addClass("invalid").removeClass("valid");

            $.toast({
                text: response.responseText,
                heading: 'Validation error',
                icon: 'error',
                showHideTransition: 'plain',
                allowToastClose: true,
                hideAfter: false,
                textAlign: 'left',
                beforeShow: function () {
                    var toastContainer = $(".toast-container");
                    toastContainer.empty();

                    var toast = $("h2.jq-toast-heading:contains('" + this.heading + "')").parent("div.jq-toast-single");
                    toastContainer.append(toast);
                }
            });
        }
    });
}