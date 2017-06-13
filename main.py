#!/usr/bin/env python3
# coding=utf-8

import logging
import os
import sys
import traceback
from getpass import getpass

from config_helper import ConfigHelper
from dualis_connector.login_helper import obtain_login_token
from dualis_connector.request_helper import RequestRejectedError, RequestHelper
from dualis_connector.results_handler import ResultsHandler
from mail_formater import create_full_diff_mail, create_full_welcome_mail, create_full_error_mail
from mail_shooter import MailShooter
from version_recorder import VersionRecorder


def run_init():
    config = ConfigHelper()

    if config.is_present():
        do_override_input = input('Do you want to override the existing config [y/n]?   ')
        while not (do_override_input == 'y' or do_override_input == 'n'):
            do_override_input_input = input('Unrecognized input. Try again:   ')

        if do_override_input == 'n':
            sys.exit(0)

    do_mail_input = input('Do you want to activate Notifications via mail [y/n]?   ')
    while not (do_mail_input == 'y' or do_mail_input == 'n'):
        do_mail_input = input('Unrecognized input. Try again:   ')

    mail_cfg = None

    if do_mail_input == 'y':
        print('[The following Inputs are not validated!]')
        sender = input('E-Mail-Address of the Sender:   ')
        server_host = input('Host of the SMTP-Server:   ')
        server_port = input('Port of the SMTP-Server:   ')
        username = input('Username for the SMTP-Server:   ')
        password = getpass('Password for the SMTP-Server [no output]:   ')
        target = input('E-Mail-Address of the Target:   ')

        mail_cfg = {
            'sender': sender,
            'server_host': server_host,
            'server_port': server_port,
            'username': username,
            'password': password,
            'target': target
        }

        print('Testing Mail-Config...')
        welcome_content = create_full_welcome_mail()
        mail_shooter = MailShooter(
            sender, server_host, int(server_port), username, password
        )
        mail_shooter.send(target, 'Hey!', welcome_content[0], welcome_content[1])
        input(
              'Please check if you received the Welcome-Mail. If yes, confirm with Return.\n'
            + 'If not, exit this program and start again.'
        )

    token = get_dualis_credentials_and_fetch_token()

    if mail_cfg is not None:
        config.set_mail_config(mail_cfg)
    config.set_token(token)

    print('Configuration finished and saved!')

    print('Fetching current state of Dualis...')
    results = fetch_current_dualis_state(token)
    recorder = VersionRecorder('_course-results')
    recorder.start_new_version()
    for course_id in results:
        recorder.save_file(course_id, results[course_id][0].prettify())
    recorder.persist_new_version()

    print('done!')

    print(
          '  To set a cron-job for this program on your Unix-System:\n'
        + '    `crontab -e`\n'
        + '    add `*/15 * * * * cd %s && python3 main.py`\n'%(os.path.dirname(os.path.realpath(__file__)))
        + '    save and done!'
    )

    print('All set and ready to go!')

def run_new_token():
    config = ConfigHelper()
    config.load()

    token = get_dualis_credentials_and_fetch_token()

    config.set_token(token)

    print('New Token successfully saved!')

def run_main():
    logging.basicConfig(
        filename='DualisWatcher.log', level=logging.DEBUG,
        format='%(asctime)s  %(levelname)s  {%(module)s}  %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info('--- main run started ---------------------')

    try:
        logging.debug('Loading config...')
        config = ConfigHelper()
        config.load()
        token = config.get_token()
    except:
        logging.error('Error while trying to load the Configuration! Exiting...')
        sys.exit(-1)

    try:
        logging.debug('Fetching current Dualis State...')
        results = fetch_current_dualis_state(token)

        logging.debug('Saving new state...')
        recorder = VersionRecorder('_course-results')
        recorder.start_new_version()
        for course_id in results:
            recorder.save_file(course_id, results[course_id][0].prettify())

        logging.debug('Checking for changes...')
        changes = recorder.changes_of_new_version()

        if changes.diff_count > 0:
            logging.info('%s changes found!'%(changes.diff_count))

            try:
                mail_cfg = config.get_mail_config()
                logging.debug('Mail-Config loaded, sending notification...')
                mail_content = create_full_diff_mail(changes, results, token)
                mail_shooter = MailShooter(
                    mail_cfg['sender'], mail_cfg['server_host'], int(mail_cfg['server_port']),
                    mail_cfg['username'], mail_cfg['password']
                )
                mail_shooter.send(
                    mail_cfg['target'], '%s neue Änderungen!'%(changes.diff_count), mail_content[0], mail_content[1]
                )
            except ValueError:
                logging.debug('No notification sent.')
                pass  # Mail_notifications not configured, ignore

        logging.debug('Saving news tate as new version...')
        recorder.persist_new_version()

        logging.debug('All done. Exiting...')
    except BaseException as e:
        error_formatted = traceback.format_exc()
        logging.error(error_formatted)
        try:
            mail_cfg = config.get_mail_config()
            logging.debug('Mail-Config loaded, sending error-notification...')
            mail_content = create_full_error_mail(str(e))
            mail_shooter = MailShooter(
                mail_cfg['sender'], mail_cfg['server_host'], int(mail_cfg['server_port']),
                mail_cfg['username'], mail_cfg['password']
            )
            mail_shooter.send(
                mail_cfg['target'], 'Fehler!', mail_content[0], mail_content[1]
            )
        except BaseException:
            logging.debug('No error-notification sent.')
            pass

        logging.debug('Exception-Handling completed. Exiting...')


def get_dualis_credentials_and_fetch_token():
    print('[The following Input is not saved, it is only used temporarily to generate a login token.]')

    token = None
    while token is None:
        dualis_username = input('Username for Dualis:   ')
        dualis_password = getpass('Password for Dualis [no output]:   ')
        try:
            token = obtain_login_token(dualis_username, dualis_password)
        except RequestRejectedError as error:
            print('Login Failed! (%s)' % (error))
        except (ValueError, RuntimeError) as error:
            print('Error while communicating with the Dualis System! (%s)' % (error))

    return token

def fetch_current_dualis_state(token):
    request_helper = RequestHelper()
    request_helper.token = token
    list_handler = ResultsHandler(request_helper)

    courses = []
    results = {}
    try:
        semesters = list_handler.fetch_semesters()
        for semester in semesters:
            courses += list_handler.fetch_courses(semester)

        for course_id in courses:
            results.update(list_handler.fetch_result(course_id))
    except (RequestRejectedError, ValueError, RuntimeError) as error:
        raise RuntimeError('Error while communicating with the Dualis System! (%s)' % (error))

    return results


# --- called at the program invocation: ---------------------
if len(sys.argv) == 2:
    if sys.argv[1] == '--init':
        run_init()
    elif sys.argv[1] == '--new-token':
        run_new_token()
    else:
        print('Invalid command!')
        sys.exit(-1)
else:
    run_main()
