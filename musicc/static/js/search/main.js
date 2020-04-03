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
let searchPage = {};
let musiccSchema = {};

$(document).ready(function () {
    attachAjaxLogoutInterceptor();
    $.ajax("/get_revision_info")
        .done((revisions) => {
            revisions.results.forEach((revision) => {
                if (revision.start_date)
                    $("#revision-selector").append($("<option>").text(revision['mus_rev']));
            });

            $("#revision-selector")
                .off("input change").on("change", (e) => loadRevision(e.currentTarget.value))
                .val($("#revision-selector option:nth-child(2)").val())
                .trigger("change");
        });

    $(document).tooltip();

    $("#advanced-options-toggle").on("click", (e) => {
        $(e.currentTarget).next(".dropdown-content").toggleClass("show");
    });
    $("#advanced-options > .dropdown-content").on("click", (e) => { e.stopPropagation() });
    $("#advanced-options #spinner").spinner({
        max: 100,
        min: 1
    }).spinner("value", 1);
    $("#spinner[name='concrete_per_logical']").on("keydown", false);
});

function loadRevision(revision) {
    $.ajax({ "url": "/get_metadata_fields", "data": { "revision": revision } })
        .done((schema) => {
            musiccSchema = schema;

            let toggledColumns = [];
            $('.underlined').each((i, element) => toggledColumns.push($(element).text()));


            $("#sidebar > form").empty();
            $("#result-table_wrapper").replaceWith('<table id="result-table" class="display" style="width:100%">');

            initialiseDataTable(schema);
            initialiseSidebar(schema);

            for (let column in toggledColumns) {
                column = toggledColumns[column];
                $('label.title').filter((i, element) => ($(element).text() === column && !$(element).hasClass("underlined"))).click();
            }

            $('label.title[value="label"], label.title[value="updateDateTime"], label.title[value="version"], label.title[value="MUSICC_ID"').not(".underlined").click();
            moveColumnToPosition("label", 1);

            validateSearchString(true);
        });
}

