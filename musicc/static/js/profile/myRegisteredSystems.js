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
function initialiseRegisteredSystemsTab() {
    initialiseRegisteredSystemsTable();

    $("#generate-registration-token-button").click(() => {
        displayTokenToCopy("/registration_token")
    });
    $("#my-registered-systems-tab").on("click", ".generate-synchronisation-token-button", (e) => {
        var instance_id = registeredSystemsTable.row($(e.target).parents('tr')).data().id;
        displayTokenToCopy("/synchronisation_token", { "id": instance_id });
    });

    $("#my-registered-systems-tab").on("click", ".deactivate-system-button", (e) => {
        var instance_id = registeredSystemsTable.row($(e.target).parents('tr')).data().id;
        deactivate_instance(instance_id);
    });

    $("#my-registered-systems-tab").on("click", ".reactivate-system-button", (e) => {
        var instance_id = registeredSystemsTable.row($(e.target).parents('tr')).data().id;
        reactivate_instance(instance_id);
    });
}
var registeredSystemsTable;
function initialiseRegisteredSystemsTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "Instance ID", data: "id" },
        { title: "Owner", data: "updated_by_user" },
        { title: "Organisation", data: "organisation" },
        { title: "Registration Time", data: "updated_date_time" },
        { title: "Active", data: "active" },
        { title: "Synchronisation" },
        { title: "manage" }
    ];

    registeredSystemsTable = $('#registered-systems-table').DataTable({
        data: [],
        columns: columns,
        columnDefs: [{
            "targets": -2,
            "data": "active",
            "render": (active) => active ? `<button class="generate-synchronisation-token-button">Generate synchronisation token</button>` : ""
        },
        {
            "targets": -1,
            "data": "active",
            "render": (active) => active ? `<button class="deactivate-system-button">Deactivate</button>` : `<button class="reactivate-system-button">Reactivate</button>`
        }],
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/system/my_registered_systems",
        }
    });
}

function deactivate_instance(instance_id) {
    $.get("/system/deactivate", { "instance_id": instance_id })
        .done((response) => {
            showSuccessToast(response);
            registeredSystemsTable.ajax.reload();
        })
        .fail((response) => {
            showErrorToast(response.responseText);
        });
}

function reactivate_instance(instance_id) {
    $.get("/system/reactivate", { "instance_id": instance_id })
        .done((response) => {
            showSuccessToast(response);
            registeredSystemsTable.ajax.reload();
        })
        .fail((response) => {
            showErrorToast(response.responseText);
        });
}

function displayTokenToCopy(url, data = undefined) {
    $.get(url, data)
        .done((token) => {
            $("<div>").append(
                $("<input class='token' type='text' readonly>").val(token)
            )
                .append(
                    $("<button class='copy-to-clipboard'>Copy to clipboard</button>").click((e) => {
                        $(e.currentTarget).siblings("input.token").select();
                        document.execCommand("copy");
                    })
                )
                .dialog()
        });
}