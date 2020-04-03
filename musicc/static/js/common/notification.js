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
$(document).ready(function () {
    $(".notification-button-text").click(() => {
        $(".notification-list").toggleClass("open");
        if (nextNotificationPage === 1) {
            loadNextPageOfNotifications();
        }
    })
    $('.notification-list').on('scroll', function () {
        if ($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            loadNextPageOfNotifications();
        }
    });
    $(window).click((e) => {
        if ($(".notification-list").hasClass("open") && !$(e.target).parents(".notification-button-container").length) {
            $(".notification-list").removeClass("open");
        }
    })
});

var nextNotificationPage = 1
function loadPageOfNotifications(pageNumber) {
    $.ajax({
        "url": "/notifications", "data": { "page": pageNumber }, "success": (data) => {
            data.notifications.forEach((notification) => {
                $(".notification-list").append(
                    `<li> <span class="notification-text ${notification.seen ? "" : "new"}">${notification.message}</span> <span class="notification-date">${notification.date.substr(0, notification.date.indexOf("T"))}</span> </li>`
                );
            });
            nextNotificationPage = data.lastPage ? -1 : data.page + 1;

            if (!$(".notification-list").hasScrollBar() && nextNotificationPage > 0) {
                loadNextPageOfNotifications();
            }

            if (data.lastPage && data.page === 1 && !data.notifications.length) {
                $(".notification-list").append(
                    `<li> You have no notifications </li>`
                );
            }
        }
    })
}


function loadNextPageOfNotifications() {
    if (nextNotificationPage > 0) {
        loadPageOfNotifications(nextNotificationPage);
    }
}

(function ($) {
    $.fn.hasScrollBar = function () {
        return this.get(0).scrollHeight > this.outerHeight();
    }
})(jQuery);