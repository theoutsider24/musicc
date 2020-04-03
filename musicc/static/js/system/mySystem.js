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
function initialiseMySystemTab() {
    $("button#register-system").click(() => {
        $("<form method='get' enctype='multipart/form-data' action='/register_system_with_master' id='registration-form'>")
            .append(
                $("<input type='text' name='token' placeholder='Registration Token'>")
            )
            .append("<p>Instance prefix:</p>")
            .append(
                $("<select name='instance_prefix'>")
                    .append($("<option value='A'>A</option>"))
                    .append($("<option value='B'>B</option>"))
                    .append($("<option value='C'>C</option>"))
                    .append($("<option value='D'>D</option>"))
                    .append($("<option value='E'>E</option>"))
                    .append($("<option value='F'>F</option>"))
                    .append($("<option value='G'>G</option>"))
                    .append($("<option value='H'>H</option>"))
                    .append($("<option value='I'>I</option>"))
                    .append($("<option value='J'>J</option>"))
                    .append($("<option value='K'>K</option>"))
                    .append($("<option value='L'>L</option>"))
                    .append($("<option value='N'>N</option>"))
                    .append($("<option value='O'>O</option>"))
                    .append($("<option value='P'>P</option>"))
                    .append($("<option value='Q'>Q</option>"))
                    .append($("<option value='R'>R</option>"))
                    .append($("<option value='S'>S</option>"))
                    .append($("<option value='T'>T</option>"))
                    .append($("<option value='U'>U</option>"))
                    .append($("<option value='V'>V</option>"))
                    .append($("<option value='W'>W</option>"))
                    .append($("<option value='X'>X</option>"))
                    .append($("<option value='Y'>Y</option>"))
                    .append($("<option value='Z'>Z</option>"))
            )
            .dialog({
                buttons: {
                    "Submit": function () {
                        $("#registration-form").submit()
                    },
                    Cancel: function () {
                        $("#registration-form").dialog("close");
                        $("#registration-form").remove();
                    }
                },
                close: function () {
                    $("#registration-form").dialog("close");
                    $("#registration-form").remove();
                }
            });
        $("form#registration-form").on('submit', function (e) {
            $.ajax({
                type: this.method,
                url: this.action,
                data: $(e.currentTarget).serialize(),
                cache: false,
                contentType: false,
                processData: false,

                success: (val) => {
                    if (typeof (val) === "object" && val.hasOwnProperty("errors") && !$.isEmptyObject(val.errors)) {
                        showErrorToast(val.errors, false);
                    }
                    else {
                        showSuccessToast(val + "<br> Reload page to see details");
                    }
                    $("#registration-form").dialog("close");
                    $("#registration-form").remove();
                },
                failure: (val) => {
                    showErrorToast(val, false);
                },
                error: (val) => {
                    showErrorToast(val.responseText, false);
                },
            });
            e.preventDefault();
        });
    })
    $("button#synchronise-system").click(() => {
        $("<form>").append(
            $("<input type='text' id='synchronise-token' placeholder='Synchronisation token'>"))
            .dialog({
                buttons: {
                    "Submit": function () {
                        if ($("#synchronise-token").val()) {
                            var info = showProgressToast("Sync in progress...");
                            $.get("/synchronise", { "token": $("#synchronise-token").val() })
                                .fail((response) => {
                                    showErrorToast(response.responseText);
                                    info.close();
                                })
                                .done((response) => {
                                    showSuccessToast(response);
                                    info.close();
                                });
                        }
                    },
                    Cancel: function () {
                        $("#synchronise-token").parents("form").dialog("close");
                        $("#synchronise-token").parents("form").remove();
                    }
                },
                close: function () {
                    $("#synchronise-token").parents("form").dialog("close");
                    $("#synchronise-token").parents("form").remove();
                }
            });
    });
}