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
}
var registeredSystemsTable;
function initialiseRegisteredSystemsTable() {
    $.fn.DataTable.ext.errMode = "throw";

    var columns = [
        { title: "Instance ID", data: "id" },
        { title: "Owner", data: "updated_by_user" },
        { title: "Organisation", data: "organisation" },
        { title: "Registration Time", data: "updated_date_time" },
        { title: "Active", data: "active" }
    ];

    registeredSystemsTable = $('#registered-systems-table').DataTable({
        data: [],
        columns: columns,
        "searching": false,
        "dom": '<"toolbar">rt<"bottom"iflp>',
        "ajax": {
            "url": "/system/registered_systems",
        }
    });
}
