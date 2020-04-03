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
function initialiseSearchbar() {

    disableDownloadButton();
    $("#search-button").off("click").click(() => $("#search-bar").submit());

    populateFilterSelector(searchableFields);
    $("#result-pane > div > select").off("change").on("change", (e) => {
        appendToSearchBar(e.currentTarget.value);
        $(e.currentTarget).val("");
    });


    $("#download-button").off("click").click(() => {
        $("#download-button-dropdown").toggleClass("show");
    });

    $("#result-pane form").off('submit').submit({
        url: '/download'
    }, (e) => {
        if ($(".ui-spinner-input[name='concrete_per_logical']").spinner("isValid")) {
            e.data.extraData = $(".ui-spinner-input[name='concrete_per_logical']").serialize()
            if ($("input#exclude_images")[0].checked) {
                e.data.extraData += "&exclude_images=true"
            }
            if ($("input#exclude_resources")[0].checked) {
                e.data.extraData += "&exclude_resources=true"
            }
        }
        submitDownloadForm(e)
    })
    $("#download-button-dropdown.dropdown-content a").off("click").click((e) => {
        let value = $(e.currentTarget).attr("value")
        $("#result-pane form").find('input[name="native"]').attr("value", value);
        $("#result-pane form").submit();
    });
    window.onclick = function (event) {
        if (!(event.target.matches('.dropbtn') || $(event.target).parents(".dropbtn").length)) {
            var dropdowns = document.getElementsByClassName("dropdown-content");
            var i;
            for (i = 0; i < dropdowns.length; i++) {
                var openDropdown = dropdowns[i];
                if (openDropdown.classList.contains('show')) {
                    openDropdown.classList.remove('show');
                }
            }
        }
    }
    enableEnterButton("#search-bar", () => $('#search-bar').submit());

    $('#search-bar')
        .off("input")
        .on("input", (event) => {
            validateSearchString(true);
        })
        .on("input focus", (e) => {
            suggestWord($(e.currentTarget))
        });

    $('#search-bar').off("keydown").on("keydown", ((e) => {
        if (e.key === "Tab") {
            selectFirstAutocompleteIfNoneSelected($(e.currentTarget).autocomplete("instance").menu.element);
            e.preventDefault();
        }
    }));

    $('#search-bar').off("submit").submit((event) => {
        let searchText = $(event.currentTarget).val();
        if (validateSearchString()) {
            performQuery(searchText);
            $(event.currentTarget).autocomplete("close");
        }
    });


    $("#result-table_wrapper").on("search:success", (event, resultSet, fileSizeString) =>
        enableDownloadButton(resultSet.query_id, fileSizeString)
    );
    $("#result-table_wrapper").on("search:failure", () =>
        disableDownloadButton()
    );
    disableEnterButton("form");
}

function getSearchBarContents() {
    return $("#search-bar").val();
}

function appendToSearchBar(queryString) {
    $("#search-bar")
        .val((getSearchBarContents().trimRight() + " " + queryString).trim())
        .removeClass("invalid");
}

function disableDownloadButton() {
    $("#download-button")
        .removeAttr('title')
        .attr("disabled", "disabled");
}

function enableDownloadButton(query_id, estimatedFileSizeString) {
    $("#result-pane form")
        .find('input[name="query_id"]').attr("value", query_id)
    $("#download-button")
        .attr('title', estimatedFileSizeString)
        .removeAttr("disabled");
}

function populateFilterSelector(fields) {
    let logical = ["AND", "OR", "NOT"];
    let comparison = ["=", "<", ">", "<=", ">=", "!=", "CONTAINS", "INCLUDES"];

    $("#result-pane > div > select > optgroup").empty();
    logical.forEach((entry) => $("select optgroup[label='Logic']").append($("<option>").attr("value", entry).text(entry)));
    comparison.forEach((entry) => $("select optgroup[label='Comparison']").append($("<option>").attr("value", entry).text(entry)));
    fields.forEach((entry) => $("select optgroup[label='Fields']").append($("<option>").attr("value", entry).text(entry)));
}

function isSearchableField(field) {
    return searchableFields.includes(field) || field.includes("CustomMetadata")
}

function stripQuotes(str) {
    if (str.slice(0, 1) === str.slice(-1) && (str.slice(-1) == `"` || str.slice(-1) == `'`))
        str = str.slice(1, -1);
    return str;
}

function validateSearchString(quiet = false) {
    let searchString = getSearchBarContents();
    // Empty searches and * searches are special cases
    if (!searchString.trim() || searchString.trim() === "*") {
        $("#search-bar").removeClass("invalid");
        return true;
    }
    let errorArray = [];
    let tokens = searchString.match(tokeniserRegex);
    let comparatorFound = false;

    tokens.forEach((token, index) => {
        let tokenIsComparator = isBinaryComparator(token);
        if (tokenIsComparator) {
            comparatorFound = true;
            let leftHandSide = tokens[index - 1];
            let rightHandSide = tokens[index + 1];
            if (!leftHandSide || !rightHandSide) {
                errorArray.push(token + " is missing an operand");
            }
            else if (isBinaryComparator(leftHandSide)) {
                errorArray.push(token + " does not have a valid left hand side");
            }
            else if (!isSearchableField(leftHandSide)) {
                errorArray.push(leftHandSide + " is not a searchable field");
            }
        }
    });
    if (!comparatorFound) {
        errorArray = ["No comparators found"];
    }
    if (errorArray.length > 0) {
        if (!quiet)
            showErrorToast(errorArray);
        $("#search-bar").addClass("invalid");
        return false;
    }
    else {
        $("#search-bar").removeClass("invalid");
        return true;
    }
}

function getCurrentWord(str) {
    return str.substring(getStartOfCurrentWord(str) + 1);
}

function getPreviousWord(str, numberOfWords = 1) {
    for (var i = 0; i < numberOfWords; i++) {
        str = str.substring(0, getStartOfCurrentWord(str)).trimRight()
    }
    str = stripQuotes(str)
    return getCurrentWord(str);
}

function getStartOfCurrentWord(str) {
    var inSingleQuotes = false;
    var inDoubleQuotes = false;
    for (var i = 0; i < str.length; i++) {
        var character = str[i];
        if (character === `"`) {
            if (!inSingleQuotes) {
                inDoubleQuotes = !inDoubleQuotes;
            }
        }
        else if (character === `'`) {
            if (!inDoubleQuotes) {
                inSingleQuotes = !inSingleQuotes;
            }
        }
    }

    var startOfWord = " "
    if (inDoubleQuotes) {
        startOfWord = `"`;
    }
    else if (inSingleQuotes) {
        startOfWord = `'`;
    }
    return str.lastIndexOf(startOfWord)
}

function suggestWord(input) {
    var currentWord = getCurrentWord(input.val());
    input.autocomplete({
        source: getWordSuggestions(input.val()),
        minLength: 0,
        select: function (event, ui) {
            var beginningOfQuery = input.val().substring(0, getStartOfCurrentWord(input.val()) + 1)
            var lastChar = beginningOfQuery.substring(beginningOfQuery.length - 1)
            var stringToInsert = ui.item.value;
            if (lastChar === `"`)
                stringToInsert = stringToInsert + `"`
            else if (stringToInsert.includes(` `) || stringToInsert.includes(`'`)) {
                stringToInsert = `"` + stringToInsert + `"`
                if (lastChar === `'`)
                    beginningOfQuery = beginningOfQuery.slice(0, -1)
            }
            else if (lastChar === `'`)
                stringToInsert = stringToInsert + `'`
            input.val(beginningOfQuery + stringToInsert + " ");
            input.one("autocompleteclose", () => { input.trigger("input") });
            event.preventDefault();
        },
        focus: () => false
    })
    input
        .autocomplete("search", currentWord)
}

function getWordSuggestions(str) {
    let logicalSymbols = ["AND", "OR"];
    let comparisonSymbols = ["=", "<", ">", "<=", ">=", "!=", "CONTAINS"];
    let allComparisonSymbols = comparisonSymbols.concat(["INCLUDES"]);

    let extras = ["NOT"]
    let searchableFieldsAndExtras = extras.concat(searchableFields)

    if (isSearchableField(getPreviousWord(str))) {
        if (musiccSchema.properties[getPreviousWord(str).split("__")[0]].array) {
            return ["INCLUDES"]
        }
        else
            return comparisonSymbols
    }
    else if (allComparisonSymbols.includes(getPreviousWord(str)) && isSearchableField(getPreviousWord(str, 2))) {
        try {
            let propertyName = getPreviousWord(str, 2)
            let properties = propertyName.split("__")
            let base_property = musiccSchema.properties[properties[0]]
            for (var i = 1; i < properties.length; i++) {
                base_property = base_property.properties[properties[i]]
            }

            return base_property.properties.value.enum ? base_property.properties.value.enum : []
        }
        catch (err) {
            return [];
        }
    }
    else if (!getPreviousWord(str) || logicalSymbols.includes(getPreviousWord(str).toUpperCase()) || extras.includes(getPreviousWord(str).toUpperCase())) {
        return searchableFieldsAndExtras
    }
    else {
        return logicalSymbols
    }
}

function selectFirstAutocompleteIfNoneSelected(list) {
    if (!list.find(".ui-state-active:visible").length) {
        list.find(".ui-menu-item-wrapper:visible").first().addClass("ui-state-active");
    }
    list.find(".ui-state-active:visible").click();
}