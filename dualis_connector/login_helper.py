from dualis_connector.request_helper import RequestHelper


def obtain_login_token(username, password) -> str:
    """
    Sends the login credentials to the Dualis-System and extracts the resulting Login-Token.
    """
    loginform_data = {
        'usrname':   username,
        'pass':      password,
        'ARGUMENTS': 'clino, usrname, pass, menuno, menu_type, browser, platform',
        'APPNAME':   'CampusNet',
        'PRGNAME':   'LOGINCHECK',
        # clino, menuno. menu_type, browser and platform are in practice ignored by the Dualis
        #  System anyway
    }

    response = RequestHelper().post_raw('/', loginform_data)[1] # = the raw response (because we
                                                                #    need to access the headers)

    refresh_instruction = response.getheader("REFRESH")
    if refresh_instruction is None:
        # = we didn't get an error page (checked by the RequestHelper) but somehow we don't have the
        #    needed header
        raise RuntimeError('Invalid response received from the Dualis System!')

    # refresh_instruction is now something like
    #  0; URL=/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=-N128917080975804,-N000019,-N000000000000000
    # ->                                                                                |<-- token -->|
    arguments_raw = refresh_instruction.split('ARGUMENTS=').pop()
    arguments = arguments_raw.split(',')

    # the token is the first argument, without the prefix '-N'
    token = arguments[0][len('-N'):]
    
    cnsc = response.getheader("Set-cookie").split('=')[1]

    return token, cnsc
