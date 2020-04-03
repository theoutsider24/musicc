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
import requests
import json
import cgi
import os.path

## Displays a cli progress bar
#  @param iteration iteration (Int)
#  @param total iterations (Int)
#  @param prefix [Optional] prefix string (Str)
#  @param suffix [Optional] suffix string (Str)
#  @param decimals [Optional] positive number of decimals in percent complete (Int)
#  @param length [Optional] character length of bar (Int)
#  @param fill [Optional] bar fill character (Str)
def print_progress_bar(
    iteration, total, prefix="", suffix="", decimals=1, length=100, fill="█"
):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    filled_length = max(filled_length, 1)

    try:
        bar = fill * filled_length + "-" * (length - filled_length)
        print("\r%s |%s| %s%% %s" % (prefix, bar, percent, suffix), end="\r")
    except UnicodeEncodeError:
        print("\r%s %s%% %s" % (prefix, percent, suffix), end="\r")
    # Print New Line on Complete
    if iteration == total:
        print()


## The MusiccSession class extends requests.Session and offers that functionality
#  with custom functionality for interaction with the MUSICC database
class MusiccSession(requests.Session):
    ## The size in bytes of chunks read when downloading files
    #  Lower chunk sizes lead to reduced download speed but lower memory usage
    CHUNK_SIZE = 8192

    ## Url for logging in
    login_url = "/accounts/login/"
    ## Url for sending queries
    query_url = "/query"
    ## Url for downloading files
    download_url = "/download"

    ## The constructor
    #  @param url The base url for all other urls
    def __init__(self, url):
        super().__init__()
        self.base_url = url

    ## Sends a post request
    #  Will raise an exception if the user isn't logged in
    #  @param url URL to send post request to
    #  @param data [optional] Data to be sent in the post request
    def post(self, url, data=None):
        response = super().post(self.base_url + url, data)
        self.check_for_login_redirect(response)
        return response

    ## Sends a get request
    #  Will raise an exception if the user isn't logged in
    #  @param url URL to send get request to
    def get(self, url="", params={}):
        response = super().get(self.base_url + url, params =  params)
        self.check_for_login_redirect(response)
        return response

    ## Downloads a file in chunks relating to a query
    #  @param result_set The query to download. This can be either a
    #  MusiccResultSet, query id or query string
    def stream_file(self, result_set):
        if isinstance(result_set, MusiccResultSet):
            query_id = result_set.query_id
        elif isinstance(result_set, int):
            query_id = result_set
        elif isinstance(result_set, str):
            result_set = self.query(result_set)
            query_id = result_set.query_id
        else:
            raise Exception("Invalid parameter")

        url = self.base_url + self.download_url
        download = super().get(url, params={"query_id": query_id}, stream=True)

        value, params = cgi.parse_header(download.headers["Content-Disposition"])
        file_size = download.headers["Content-Length"]
        filename = params["filename"]
        if os.path.exists(filename):
            raise Exception("File " + filename + " already exists")
        with open(filename, "wb") as target_file:
            print("Downloading...")
            i = 0
            for chunk in download.iter_content(chunk_size=self.CHUNK_SIZE):
                print_progress_bar(i, int(int(file_size) / self.CHUNK_SIZE))
                i += 1
                if chunk:  # filter out keep-alive new chunks
                    target_file.write(chunk)

    ## Raises an exception if a response shows a redirect to the login page
    #  @param response Response from a query
    def check_for_login_redirect(self, response):
        # If we were redirected to the login page, we're not logged in
        if self.login_url in response.url:
            raise Exception("Session is not logged in")

    ## Sends query string to the query url and constructs a MusiccResultSet object
    #  @param query_string Query to execute
    def query(self, query_string):
        response = self.get(self.query_url, {"query": query_string})
        return MusiccResultSet(response)

    ## Logs in the current session with the given credentials
    #  @param username Username
    #  @param password Password
    def login(self, username, password):
        try:
            self.get()
        except:
            pass
        if "csrftoken" in self.cookies:
            try:
                return self.post(
                    self.login_url,
                    {
                        "username": username,
                        "password": password,
                        "csrfmiddlewaretoken": self.cookies["csrftoken"],
                    },
                )
            except:
                raise Exception("Login failed")


## The MusiccResultSet class represents the data returned from a query
class MusiccResultSet:
    ## The constructor
    #  @param response The JSON response to a query
    def __init__(self, response):
        self.json_result_set = json.loads(response.content)
        self.count = self.json_result_set["recordsFiltered"]
        self.query_id = self.json_result_set["query_id"]
        self.estimated_download_size = self.json_result_set["estimatedDownloadSize"]
        self.estimated_resources_size = self.json_result_set["estimatedResourcesSize"]
        self.estimated_images_size = self.json_result_set["estimatedImagesSize"]
        self.query_id = self.json_result_set["query_id"]
        self.results = self.json_result_set["results"]

