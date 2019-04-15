import re
import urllib
from http.client import HTTPSConnection, HTTPResponse

from bs4 import BeautifulSoup


class RequestHelper:
    """
    Encapsulates the recurring logic for sending out requests to the Dualis-System.
    """
    def __init__(self, token = '', cnsc = '0'):
        self.connection = HTTPSConnection('dualis.dhbw.de')
        self.token = token
        self.stdHeader = {
            'Cookie': 'cnsc=' + cnsc,
            # The Dualis System assumes by the presence of this field that we are ready to handle
            #   and store cookies
            #  Yeah, right... We definitively do that...
            #  (No, we don't have to. Chrome is also sending cnsc=0 everytime and it works fine)
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            # copied straight out of Chrome
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
            id_segment = '-N' + id
        else:
            id_segment = ''

        self.connection.request(
            'GET',
            '/scripts/mgrqispi.dll?APPNAME=CampusNet&PRGNAME=%s&ARGUMENTS=-N%s,-N000019,%s'%(
                programName, self.token, id_segment
            ),
            headers=self.stdHeader
        )
        
        response = self.connection.getresponse()
        return self._initial_parse(response)

    def post_raw(self, relative_url: str, data: object) -> (BeautifulSoup, HTTPResponse):
        """
        Sends data via POST to the Dualis System
        @param relativeUrl: the Endpoint-Url to which the data should be send, relative to /scripts/mgrqispi.dll
        @param data: a plain object representing the data to post
        @return: the response returned by the Dualis System, already checked for errors
        """
        data_urlencoded = urllib.parse.urlencode(data)

        self.connection.request(
            'POST',
            '/scripts/mgrqispi.dll%s'%(
                relative_url
            ),
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
            error = response_soup.findAll('h3')[-1].find('div').string
            if ('Program not found' in error):
                raise ValueError('The requested program could not be found by the Dualis System!')
            elif ('Aborting context' in error):
                raise DualisSleepingError('Request Context was aborted.')
            else:
                raise RuntimeError('An Unexpected Error happened on side of the Dualis System! Details: %s'%(error))

        if (response_soup.find('form', id='cn_loginForm') is not None):
            # If an error with the token or the login itself occurs, we get thrown back to the login
            #  page with an additional error message.
            # (In other error-cases we just get a page with nonsensical data back, which is
            #  not easily distinguishable from a valid response and not indicated as an error in any
            #  way...)
            response_maincontent = response_soup.body.find('div', id='pageContent')

            error_title = response_maincontent.find('h1')
            error_description = error_title.next_sibling
            error_title = self._remove_special_html_elements(error_title.string)
            error_description = self._remove_special_html_elements(error_description.string)

            raise RequestRejectedError(
                'The Dualis System rejected the Request. Details: %s%s'%(
                    error_title, ' (' + error_description + ')' if (error_description != '') else ''
                )
            )

        return response_soup

    def _remove_special_html_elements(self, string) -> str:
        string_without_htmltags = re.sub(r'(</?[a-zA-Z ]+/?>)', '', string)
        string_without_special_elements = re.sub('&[a-zA-Z]+;', ' ', string_without_htmltags)
        return string_without_special_elements.strip('\n').strip(' ')
        #                                      ^ because i.e. the error-text has a dangling new-line


class RequestRejectedError(Exception):
    """An Exception which gets thrown if the Dualis-System answered with an Error to our Request"""
    pass

class DualisSleepingError(Exception):
    """An Exception used for aborting when Dualis is sleeping again at night"""
    pass
