# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
from query import MusiccSession


def main():
    url = "http://musicc.ts-catapult.org.uk"
    username = "musicc1"
    password = "pass"

    with MusiccSession(url) as session:
        session.login(username, password)

        # Execute search then download results
        result_set = session.query("CountryCode = Gb")
        session.stream_file(result_set)

        # Download files related to a particular query_id
        session.stream_file(1)

        # Execute query and download results
        session.stream_file("CountryCode = IE")


if __name__ == "__main__":
    main()
