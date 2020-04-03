$(document).ready(function () {
    $("body").append($(`<div id="detail-view"/>`))
    $("#detail-view").dialog({
        resizable: false,
        autoOpen: false,
        height: window.innerHeight - 100,
        width: "calc(100% - 50px)",
        modal: true,
        closeOnEscape: false,
        draggable: false,
        close: function (event, ui) { location.hash = "" }
    });
    // Resize the detail view if the browser window is resized
    $(window).resize(function () {
        $("#detail-view").dialog("option", "height", window.innerHeight - 100);
    });
    // If a hash anchor change is detected in the url, reload the detail view
    window.addEventListener("hashchange", reload, false);
    reload();
});

function loadDetailView(id) {
    // Either use the provided id or look for an anchor
    if (!id) {
        id = location.hash.replace('#', '')
    }
    if (id) {
        $("#detail-view").load("/search/detail", {
            id: id,
            csrfmiddlewaretoken: getCookie("csrftoken")
        }, (html, status) => {
            if (status === "success") {
                $("#detail .tabs").tabs();
                $("#detail-view").dialog("open");

                // Remove any non-text content in the file viewers
                $("#mus-tab, #osc-tab, #odr-tab").find(".file-viewer").each((i, element) => {
                    element = $(element);
                    var xmlString = element.text().trim();
                    element.empty();
                    element.text(xmlString);
                });
                // Handle special hover behaviour for tag box
                $("#tag-container").on("mouseenter", (e) => {
                    $(e.currentTarget).css($(e.currentTarget).position()).css({ position: "absolute", height: "auto" });
                    $("#revision").css({ "margin-left": "220px" });
                });
                $("#tag-container").on("mouseleave", (e) => {
                    if (!$("#tag-container > span").length) {
                        $(e.currentTarget).css({ top: "", left: "", position: "", height: "" });
                        $("#revision").css({ "margin-left": "" });
                    }
                });
                // Replace the metadata text with a formatted version
                var formattedJson = $("<div>");
                formattedJson.jsonTable(JSON.parse($("#metadata-tab > div").text()), {
                    arrayIndex: false
                });
                $("#metadata-tab > div").empty().append(formattedJson);
                // When horizontal scrolling is used on the header, reposition any visible dropdowns to follow
                $("#detail > div:nth-child(1)").on("scroll", () => {
                    var { top: top_rev, left: left_rev } = $("#revision-button").position();
                    $("#revision-button-dropdown.show").css({ top: top_rev, left: left_rev });

                    var { top: top_dl, left: left_dl } = $("#download > button").position();
                    $("#individual-download-button-dropdown.show").css({ top: top_dl + 28, left: left_dl });

                    $("#tag-container").css($("#tags").position());
                })

                $("#detail")
                    .on("click", "#revision-button a", (e) => {
                        var pos = $(e.currentTarget).parent().position()
                        $("#revision-button-dropdown").toggleClass("show").css({ top: pos.top, left: pos.left });
                    })
                    .on("click", "#version > span > a", () => {
                        $("[href='#history-tab']").click();
                    })
                    .on("click", "#download #individual-download-button-dropdown a", (e) => {
                        let value = $(e.currentTarget).attr("value")
                        $("#detail #download form")
                            .find('input[name="native"]')
                            .attr("value", value).submit();
                    })
                    .on("submit", "#download form", { url: '/download/individual' }, submitDownloadForm)
                    .on("click", "#download > button", (e) => {
                        var pos = $(e.currentTarget).position();
                        $("#individual-download-button-dropdown").toggleClass("show").css({ top: pos.top + 28, left: pos.left });
                    })
                    .on("change", ".diff-selector", (e) => {
                        var versionSelector = $(e.currentTarget).find("select")
                        // The version to compare are the one we're currently viewing and the one that has been selected
                        var versions = [$("#version > span").text(),
                        versionSelector.val()]
                        versions.sort()

                        if (!isNaN((versionSelector.val()))) {
                            addDiffTab(versions[0],
                                versions[1],
                                $(e.currentTarget).attr("type"));
                            versionSelector.val("-");
                        }
                    })
                    .on("click", "span.ui-icon-close", function (e) {
                        // When a tab is closed, open the one that appears before it
                        var previousTab = undefined;
                        if ($(e.currentTarget).closest("li").hasClass("ui-state-active")) {
                            previousTab = $(e.currentTarget).closest("li").prev("li").find("a");
                        }
                        var panelId = $(e.currentTarget).closest("li").remove().attr("aria-controls");
                        $("#" + panelId).remove();
                        $(e.currentTarget).parent(".tabs").tabs("refresh");
                        if (previousTab) {
                            previousTab.click();
                        }
                    })
                    .on("click", "#history-tab tr:not(.ui-state-active)", (e) => {
                        // If a history-tab row is clicked, open the corresponding musicc file in the file viewer
                        load($(e.currentTarget).attr("mus_id"));
                    })
                    .on("click", "#history-tab td div.file", (e) => {
                        // If a history-tab file element is clicked, open the corresponding file in the file viewer
                        let type = $(e.currentTarget).attr("type")
                        openTabByTarget(`${type}-tab`);
                    })
                    .on("click", ".tabs.left a.ui-tabs-anchor", (e) => {
                        // When a tab is focussed in the file viewer, reflect the selection in the history view
                        if ($(e.currentTarget).text().includes("diff")) {
                            var v1 = $(e.currentTarget).attr("v1")
                            var v2 = $(e.currentTarget).attr("v2")
                            var fileType = $(e.currentTarget).attr("type")
                            $(".file.diff").removeClass("diff");
                            $(".file.ui-state-active").removeClass("ui-state-active");
                            $(`tr[version=${v1}]`).find(`.file[type=${fileType}]`).addClass("diff");
                            $(`tr[version=${v2}]`).find(`.file[type=${fileType}]`).addClass("diff");
                        }
                        else {
                            var tab = $($(e.currentTarget).attr("href"));
                            var targetFile = `#${tab.attr("type")}-${tab.attr("file_id")}`

                            if ($(`#history-tab ${targetFile}`).length) {
                                $(".file.diff").removeClass("diff");
                                $(".file.ui-state-active").removeClass("ui-state-active");
                                $(`#history-tab ${targetFile}`).addClass("ui-state-active");
                            }
                        }
                    })
                    .on("submit", ".comment-text-area form", (e) => {
                        e.preventDefault();
                        $.ajax({ "url": "/search/detail/comment", "data": $(e.currentTarget).serialize() }).done(() => {
                            reload();
                        });

                    })
                    .on("click", "#discussion-tab .controls input[type='checkbox']", function (e) {
                        if (e.currentTarget.checked) {
                            var currentVersion = $("#version > span").text();
                            $(`div.comment:not([version='${currentVersion}'])`).hide();
                        }
                        else {
                            $(`div.comment`).show();
                        }
                    }).on("click", "#discussion-tab .comment-text-area input[type='checkbox']", function (e) {
                        $("#discussion-tab .comment-text-area input[name='is_broken']").attr("value", String($(e.currentTarget).is(":checked")));
                    })
                    .on("click", "#discussion-tab .controls .moderator", function (e) {
                        var button = $(e.currentTarget);
                        $.ajax({ "url": `search/detail/comment/${button.attr("action")}`, "data": { id: $("#detail-view #detail").attr("mus_id") } }).done(() => {
                            reload();
                        });
                    })
                    .on("click", "#tags .ui-icon-plus", (e) => {
                        if (!$("#tag-container > span[contenteditable='true']").length) {
                            var editor = $(`<span contenteditable="true"></span>`)
                            $(e.currentTarget).before(editor);

                            var tagList = musiccSchema.properties.Tags.properties.Tag.properties.value.enum
                            var existingTags = [];
                            $("#tag-container > div.tag").each((i, item) => existingTags.push($(item).text().trim()));

                            editor.autocomplete({ source: tagList.filter(tag => !existingTags.includes(tag)) });
                            var submitTag = function (tagText) {
                                $.ajax({
                                    "url": "search/detail/tag/add", "data": { "id": $("#detail-view #detail").attr("mus_id"), "tag": tagText }, "success": () => {
                                        $("#tag-container > span[contenteditable='true']").remove();
                                        $("#tag-container .ui-icon-plus").before($(`<div class="tag">${tagText}<div class="ui-icon ui-icon-close"></div></div>`));
                                        if (!tagList.includes(tagText)) {
                                            tagList.push(tagText);
                                        }
                                    }, "error": () => { $("#tag-container > span[contenteditable='true']").remove(); }
                                });
                            }
                            editor.focus().on('keypress', function (e) {
                                if (e.which == 13) {
                                    var tagText = $("#tag-container > span[contenteditable='true']").text().trim();
                                    if (tagText) {
                                        submitTag(tagText)
                                    }
                                    e.preventDefault();
                                }
                            }).keyup(function (e) {
                                if (e.key == "Escape") {
                                    $(e.currentTarget).remove();
                                    $("#tag-container").css({ top: "", left: "", position: "", height: "" });
                                }
                            }).on("autocompleteselect", function (event, item) {
                                submitTag(item.item.value);
                            });
                        }
                        // Tag Added 
                    })
                    .on("click", "#tags .ui-icon-close", (e) => {
                        var tagName = $(e.currentTarget).parent().text().trim();
                        $.ajax({
                            "url": "search/detail/tag/remove", "data": { "id": $("#detail-view #detail").attr("mus_id"), "tag": tagName }, "success": () => {
                                $(e.currentTarget).parent().remove();
                            }
                        });
                    })
                    .on("click", "#header > #favourite .favorite-star-character", (e) => {
                        if ($(e.currentTarget).attr("active") !== "") {
                            $.ajax({
                                "url": "search/detail/tag/add", "data": { "id": $("#detail-view #detail").attr("mus_id"), "tag": "favourite" }, "success": () => {
                                    $(e.currentTarget).attr("active", "");

                                    var revision = $("#revision #revision-button").text().trim();
                                    var label = $("#label").text().trim();
                                    $(searchPage.dataTable.row((i, data) => data.metadata.revision === revision && data.metadata.label === label).node()).find(".favorite-star-character").attr("active", "");
                                }
                            });
                        }
                        else {
                            $.ajax({
                                "url": "search/detail/tag/remove", "data": { "id": $("#detail-view #detail").attr("mus_id"), "tag": "favourite" }, "success": () => {
                                    $(e.currentTarget).removeAttr("active");
                                    var revision = $("#revision #revision-button").text().trim();
                                    var label = $("#label").text().trim();
                                    $(searchPage.dataTable.row((i, data) => data.metadata.revision === revision && data.metadata.label === label).node()).find(".favorite-star-character").removeAttr("active");
                                }
                            });
                        }
                    });
                bindContextMenu();
                $("#detail-view").trigger("detail:load");
            }
            else {
                showErrorToast(`Detail view could not be loaded for scenario #${id}<br>It may have been deleted or not yet approved`)
            }
        })
    }
    else {
        $("#detail-view").dialog("close");
    }
}

function reload() {
    load();
}

function load(id, targetTab) {
    if ($("#detail-view").length && $("#detail-view").dialog("isOpen")) {
        var revision = $("#revision span").text().trim();
        var openTabHrefLeft = $(".tabs.left li.ui-state-active a").attr("href").substring(1);
        var openTabHrefRight = $(".tabs.right li.ui-state-active a").attr("href").substring(1);
        var diffTabs = []
        $("a:contains('diff')")
            .each((i, a) => {
                diffTabs.push({
                    "v1": $(a).attr("v1"),
                    "v2": $(a).attr("v2"),
                    "fileType": $(a).attr("type"),
                    "diff": $($(a).attr("href"))
                })
            });

        var checkBoxStates = $("#detail input[type='checkbox']").map(function () {
            return { "id": this.id, "checked": $(this).is(":checked") };
        }).get();
        var selectedDiffTab = $(".tabs.left li.ui-state-active a:contains('diff')").text()

        $("#detail-view").one("detail:load", () => {
            if (revision === $("#revision span").text().trim()) {
                diffTabs.forEach((diff) => addDiffTab(diff.v1, diff.v2, diff.fileType, diff.diff));
            }
            openTabByTarget(openTabHrefLeft);
            openTabByTarget(openTabHrefRight);
            if (selectedDiffTab)
                $(`a:contains("${selectedDiffTab}")`).click()
            checkBoxStates.forEach((state) => {
                if (state.id && $(`#${state.id}`).prop("checked") !== state.checked) {
                    $(`#${state.id}`).click();
                }
            });
            openTabByTarget(targetTab);
        })
    }
    if (!id) {
        loadDetailView();
    }
    else {
        location.hash = id;
    }

}


var tabCounter = 1;
function addDiffTab(v1, v2, fileType, preparedDiff) {
    var tabs = $("#detail .tabs.left").tabs()
    var label = `${fileType} diff - ${v1}->${v2}`,
        id = "tabs-" + tabCounter,
        linkId = `${fileType}-${v1}-${v2}`,
        li = `<li id="${linkId}"><a href='#${id}' v1="${v1}" v2 ="${v2}" type="${fileType}">${label}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>`

    if ($(`#${linkId}`).length) {
        $(`#${linkId} a`).click();
    }
    else {
        tabs.find(".ui-tabs-nav").append(li);
        tabs.append("<div id='" + id + "' class='diff-tab'></div>");
        if (!preparedDiff) {
            displayDiff(v1, v2, fileType, $("#" + id))
        }
        else {
            $("#" + id).append(preparedDiff)
        }
        tabs.tabs("refresh");
        tabCounter++;
        if (!preparedDiff) {
            openTabByTarget(id);
        }
    }
}

function openTabByTarget(targetId) {
    $(`[href='#${targetId}']`).click();
}

function bindContextMenu() {
    // Trigger action when the contexmenu is about to be shown
    $("#history-tab .file").on("contextmenu", function (event) {
        var targetFile = $(event.currentTarget);
        $(".custom-menu").data("target", targetFile)

        // Avoid the real one
        event.preventDefault();

        $(".custom-menu > li").removeClass("disabled");

        // If file has no previous version, disable diff with Previous
        if (!targetFile.parents("tr").nextAll("tr").find(`.file[type='${targetFile.attr("type")}']`).last().length) {
            $("li[data-action='diff-prev']").addClass("disabled");
        };

        // If file is already open, disable View File
        if (targetFile.hasClass("ui-state-active")) {
            $("li[data-action='view']").addClass("disabled");
        }

        // If no file selected or selected file has different type, disable compare with selected
        if (!$(".file.selected").length || $(".file.selected").attr("type") !== targetFile.attr("type") || targetFile.hasClass("selected")) {
            $("li[data-action='diff-compare']").addClass("disabled");
        }

        // Show contextmenu
        $(".custom-menu").finish().toggle(100).
            // In the right position (the mouse)
            css({
                top: event.pageY + "px",
                left: event.pageX + "px"
            });
    });


    // If the document is clicked somewhere
    $(document).on("mousedown", function (e) {
        // If the clicked element is not the menu
        if (!$(e.target).parents(".custom-menu").length > 0) {
            // Hide it
            $(".custom-menu").hide(100);
        }
    });


    // If the menu element is clicked
    $(".custom-menu").on("click", "li:not(.disabled)", function () {

        var targetFile = $(".custom-menu").data("target");
        // This is the triggered action name
        switch ($(this).attr("data-action")) {
            // A case for each action. Your actions here
            case "view": targetFile.click(); break;
            case "diff-prev":
                var previousFile = targetFile.parents("tr").nextAll("tr").find(`.file[type='${targetFile.attr("type")}']`).first();
                if (previousFile.length) {
                    var targetVersion = previousFile.parents("tr").attr("version");
                    var selectedVersion = targetFile.parents("tr").attr("version");
                    var versions = [selectedVersion,
                        targetVersion]
                    versions.sort();
                    addDiffTab(versions[0],
                        versions[1],
                        targetFile.attr("type"));
                }

                break;
            case "diff-select":
                $(".file.selected").removeClass("selected");
                targetFile.addClass("selected");
                break;
            case "diff-compare":
                var targetVersion = targetFile.parents("tr").attr("version");
                var selectedVersion = $(".file.selected").parents("tr").attr("version");
                var versions = [selectedVersion,
                    targetVersion]
                versions.sort();
                addDiffTab(versions[0],
                    versions[1],
                    targetFile.attr("type"));
                $(".file.selected").removeClass("selected");
                break;
        }

        // Hide it AFTER the action was triggered
        $(".custom-menu").hide(100);
    });
}

function displayDiff(v1, v2, fileType, container) {
    $.ajax({
        "url": "/search/detail/diff",
        "data": {
            v1: v1,
            v2: v2,
            label: $("#label").text().trim(),
            revision: $("#revision-button").text().trim(),
            file_type: fileType
        }
    }).done((data) => {

        //Remove second line which is blank but shouldn't be
        var lines = data.split('\n');
        lines.splice(1, 1);
        data = lines.join('\n');

        var diffHtml = Diff2Html.getPrettyHtml(data,
            { inputFormat: 'diff', showFiles: false, matching: 'lines', outputFormat: 'line-by-line' }
        );

        container.html(diffHtml);
    });
}