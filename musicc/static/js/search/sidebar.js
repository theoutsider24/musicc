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
var searchableFields = []
function initialiseSidebar(schema) {
    createJsonForm(schema)

    $("form .controls")
        .append(
            $("<button>")
                .text("OR")
                .click(addQueryToSearch))
        .append(
            $("<button>")
                .text("AND")
                .click(addQueryToSearch));

    // If enter is pressed on a sidebar input field, trigger the first sibling button
    enableEnterButton(".controls input", (event) => $($(event.currentTarget).siblings("button")[0]).click());

    $("#sidebar-collapse-controls-minimise").off("click").click(toggleMinimisedSidebar);

    initialiseSearchbar();
}

function createJsonForm(schema) {
    searchableFields = []
    $('#sidebar > form').jsonForm({
        schema: schema,
        form: "*",
        onSubmit: function (errors, values) {
        }
    });

    $(".jsonform-error-CustomMetadata").remove();
    $("form .form-group > label").each((index, element) => {
        let validValueFields = []
        for (var field in schema.properties) {
            if (field
                && schema.properties[field].type === "object"
                && schema.properties[field].properties.hasOwnProperty("value")
                && Object.keys(schema.properties[field].properties).length !== 1) {

                validValueFields.push(field)
            }
        }
        element = $(element);
        if (!(validValueFields.includes(element.text().split(".")[0]))) {
            element.text(element.text().replace(".value", ""));
        }
        element.text(element.text().replace(".", "__"))
            .attr("for", "")
            .addClass("title");
        searchableFields.push(element.text())

        element.before("<input type='checkbox'>");
        element.siblings("input[type='checkbox']").off("click").on("click", (e) => {
            toggleColumn(element.text().split(".")[0]);
            $(e.currentTarget).parents("div > .form-group").find("label.title").toggleClass('underlined');
            var isChecked = $(e.currentTarget).prop("checked");
            $(e.currentTarget).parents("div > .form-group").find(":not(label) > input[type='checkbox']").prop("checked", isChecked);
        });

        element.off("click").click((e) => {
            element.siblings("input[type='checkbox']").click();
        });


        element.attr("value", element.text());
        if (schema.properties[element.text().split("__")[0]].array) {
            element.addClass("array");
            element.text(element.text().split("__")[0]);
        }
        element.text(element.text().split("__").join("."));

    });
}

function isBinaryComparator(token) {
    let binaryComparators = ["=", "==", "<", ">", "<=", ">=", "!=", "contains", "includes"];
    return binaryComparators.includes(token.toLowerCase());
}

function addQueryToSearch(event) {
    var button = $(event.currentTarget);
    var combinator = button.text();
    var fieldLabel = button.parent().siblings("label");
    var fieldName = fieldLabel.attr("value");
    var fieldValue = button.siblings("input, select").val();
    if (typeof fieldValue === "undefined") {
        fieldValue = button.siblings(".checkbox").find("input").is(":checked") ? "True" : "False"
    }

    var operator = "=";
    if (fieldLabel.hasClass("array")) {
        operator = "INCLUDES";
    }

    if (button.siblings("input[type=datetime-local]").length) {
        operator = "CONTAINS";
    }

    if (fieldValue) {
        if (getSearchBarContents())
            appendToSearchBar(combinator + " ");
        appendToSearchBar(fieldName + " " + operator + ` "` + fieldValue + `"`);
    }
}

function toggleMinimisedSidebar() {
    $("#sidebar, #result-pane").toggleClass("minimised-sidebar");

    $("#sidebar-collapse-controls-minimise .arrow").toggleClass("left").toggleClass("right");
    $("#result-pane").on('transitionend', () => searchPage.dataTable.columns.adjust());
}
