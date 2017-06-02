from http.client import HTTPSConnection, HTTPResponse
import urllib
from bs4 import BeautifulSoup
import re


class RequestHelper:
    def __init__(self):
        self.connection = HTTPSConnection('dualis.dhbw.de')
        self.token = ''
        self.stdHeader = {
            'Cookie': 'cnsc=0',
            # the Dualis System assumes by the presence of this field that we are ready to handle and store cookies
            # yeah, right... we definitively do that...
            # (no, we don't have to. Chrome is also sending cnsc=0 everytime and it works fine)
        }

    def get_ressource(self, programName: str, id: str = None) -> BeautifulSoup:
        """
        Sends a GET-Request to the Dualis System
        @param programName: The name of the Dualis sub-program to call, as expected by PRGNAME.
        @param id: The optional id in the ARGUMENTS list for the sub-program.
        @return: The response returned by the Dualis System, already checked for errors.
        """

        if (self.token is None):
            raise ValueError('The required Token is not set!')

        if (id is not None):
            id_segment = ',-N' + id
        else:
            id_segment = ','

        self.connection.request(
            'GET',
            '/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME='
                + programName
                + '&ARGUMENTS='
                + '-N' + self.token
                + ',-N000019'
                + id_segment,
            headers=self.stdHeader
        )

        response = self.connection.getresponse()

        return self._initial_parse(response)

    def post_raw(self, relative_url: str, data: object) -> (BeautifulSoup, HTTPResponse):
        """
        Sends data via POST to the Dualis System
        @param relativeUrl: the Endpoint-Url to which the data should be send, relative to /scripts/mgrqcgi
        @param data: a plain object representing the data to post
        @return: the response returned by the Dualis System, already checked for errors
        """
        data_urlencoded = urllib.parse.urlencode(data)

        self.connection.request(
            'POST',
            '/scripts/mgrqcgi' + relative_url,
            body=data_urlencoded,
            headers=self.stdHeader
        )

        response = self.connection.getresponse()

        return self._initial_parse(response), response

    def _initial_parse(self, response):
        if (response.getcode() != 200):
            raise RuntimeError('An Unexpected Error happened on side of the Dualis System!')

        response_soup = BeautifulSoup(response.read(), 'html.parser')

        if (    response_soup.title is not None
            and response_soup.title.string == 'Execution Error'
        ):
            if (response_soup.find('font', string=re.compile(r'.*(-131).*')) is not None):
                raise ValueError('The requested program could not be found by the Dualis System!')
            else:
                raise RuntimeError('An Unexpected Error happened on side of the Dualis System!')

        if (response_soup.find('form', id='cn_loginForm') is not None):
            # if an error with the token or the login itself occurs, we get thrown back to the login page
            # (in other cases we just get a page with nonsensical data back)
            response_maincontent = response_soup.body.find('div', id='pageContent')

            error_title = response_maincontent.h1
            error_description = error_title.next_sibling
            error_title = self._remove_special_html_elements(error_title.string)
            error_description = self._remove_special_html_elements(error_description.string)

            raise RequestRejectedError(
                'The Dualis System rejected the Request. Details: %s %s'
                    %(error_title, '(' + error_description + ')' if (error_description != '') else '')
            )

        return response_soup

    def _remove_special_html_elements(self, string):
        string_without_htmltags = re.sub(r'(</?[a-zA-Z ]+/?>)', '', string)
        return re.sub('&nbsp;', ' ', string_without_htmltags).strip('\n').strip()


class RequestRejectedError(Exception):
    """An Exception thrown if the Dualis-System answered with an Error to our Request"""
    pass