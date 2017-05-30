"""
This Module provides the Functionality for executing the login into the Dualis System, resulting in the obtainment of a
login token (or an exception if the login is invalid).
"""
import urllib
from http.client import HTTPSConnection


def obtain_login_token(username, password):
    connection = HTTPSConnection('dualis.dhbw.de')

    loginform_data = urllib.parse.urlencode({
        'usrname':   username,
        'pass':      password,
        'ARGUMENTS': 'clino, usrname, pass, menuno, menu_type, browser, platform',
        'APPNAME':   'CampusNet',
        'PRGNAME':   'LOGINCHECK',
        # clino, menuno and menu_type change, but the Dualis-Program apparently doesn't care about them at all
        # browser and platform are never set
        # TODO: Get these values out of hidden form fields on https://dualis.dhbw.de/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=EXTERNALPAGES&ARGUMENTS=-N000000000000001,-N000324,-Awelcome
    })
    loginform_headers = {
        'Cookie': 'cnsc=0',
        # the Dualis System assumes by the presence of this field that we are ready to handle and store cookies
        # yeah, right... we definitively do that...
    }
    connection.request('POST', '/scripts/mgrqcgi', body=loginform_data, headers=loginform_headers)

    response = connection.getresponse()
    refresh_instruction = response.getheader("REFRESH")
    if refresh_instruction is None:
        raise ValueError('Invalid login data!')

    # refresh_instruction is now something like
    #    0; URL=/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=-N128917080975804,-N000019,-N000000000000000
    # ->                                                                                  |<-- token -->|
    params_raw = refresh_instruction.split('?')[1].split('&')
    params = dict(param_raw.split('=') for param_raw in params_raw)
    application_arguments = params["ARGUMENTS"].split(',')

    # the token is the first argument, omitting the prefix '-N'
    token = application_arguments[0][len('-N'):]

    return token