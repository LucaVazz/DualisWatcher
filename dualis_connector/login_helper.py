"""
This Module provides the Functionality for executing the login into the Dualis System, resulting in the obtainment of a
login token (or an exception if the login is invalid).
"""
from dualis_connector.request_helper import RequestHelper, RequestRejectedError


def obtain_login_token(username, password):
    loginform_data = {
        'usrname':   username,
        'pass':      password,
        'ARGUMENTS': 'clino, usrname, pass, menuno, menu_type, browser, platform',
        'APPNAME':   'CampusNet',
        'PRGNAME':   'LOGINCHECK',
        # clino, menuno. menu_type, browser and platform are in practice ignored by the Dualis System anyway
    }

    response = RequestHelper().post_raw('/', loginform_data)[1] # = the raw response
                                                                #   (because we need to access the headers)

    refresh_instruction = response.getheader("REFRESH")
    if refresh_instruction is None:
        raise RuntimeError('Invalid response received from the Dualis System!')

    # refresh_instruction is now something like
    #    0; URL=/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=-N128917080975804,-N000019,-N000000000000000
    # ->                                                                                  |<-- token -->|
    params_raw = refresh_instruction.split('?')[1].split('&')
    params = dict( raw_element.split('=') for raw_element in params_raw )
    application_arguments = params["ARGUMENTS"].split(',')

    # the token is the first argument, without the prefix '-N'
    token = application_arguments[0][len('-N'):]

    return token
