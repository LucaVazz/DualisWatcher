#!/usr/bin/env python3
# coding=utf-8

import logging
import os
import sys
import traceback

from config_helper import ConfigHelper
from dualis_connector.dualis_service import DualisService
from notification_services.mail.mail_service import MailService


class ReRaiseOnError(logging.StreamHandler):
    """
    A logging-handler class which allows the exception-catcher of i.e. PyCharm to intervine
    """
    def emit(self, record):
        if hasattr(record, 'exception'):
            raise record.exception
        else:
            raise RuntimeError(record.msg)


def run_init():
    config = ConfigHelper()

    if config.is_present():
        do_override_input = input('Do you want to override the existing config [y/n]?   ')
        while not (do_override_input == 'y' or do_override_input == 'n'):
            do_override_input = input('Unrecognized input. Try again:   ')

        if do_override_input == 'n':
            sys.exit(0)

    MailService(config).interactively_configure()

    dualis = DualisService(config)
    dualis.interactively_acquire_token()

    print('Configuration finished and saved!')

    print('Fetching current state of Dualis...')
    dualis.fetch_and_save_unchecked_state()
    print('done!')

    print(
          '  To set a cron-job for this program on your Unix-System:\n'
        + '    1. `crontab -e`\n'
        + '    2. Add `*/15 * * * * cd %s && python3 main.py`\n'%(os.path.dirname(os.path.realpath(__file__)))
        + '    3. Save and you\'re done!'
    )

    print('All set and ready to go!')

def run_new_token():
    config = ConfigHelper()
    config.load()  # because we do not want to override the other settings

    DualisService(config).interactively_acquire_token()

    print('New Token successfully saved!')

def run_main():
    logging.basicConfig(
        filename='DualisWatcher.log', level=logging.DEBUG,
        format='%(asctime)s  %(levelname)s  {%(module)s}  %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info('--- main started ---------------------')
    if IS_DEBUG:
        logging.info('Debug-Mode detected. Errors will not be logged but instead re-risen.')
        debug_logger = logging.getLogger()
        debug_logger.setLevel(logging.ERROR)
        debug_logger.addHandler(ReRaiseOnError())
        logging.info('nice')

    try:
        logging.debug('Loading config...')
        config = ConfigHelper()
        config.load()
    except BaseException as e:
        logging.error('Error while trying to load the Configuration! Exiting...', extra={'exception':e})
        sys.exit(-1)

    mail_service = MailService(config)

    try:
        dualis = DualisService(config)

        results = dualis.fetch_and_check_state()
        changes = results[0]
        course_names = results[1]

        if changes.diff_count > 0:
            logging.info('%s changes found!'%(changes.diff_count))

            token = dualis.get_token()
            mail_service.notify_about_changes_in_results(changes, course_names, token)

            dualis.save_state()
        else:
            logging.info('No changes found.')

        logging.debug('All done. Exiting...')
    except BaseException as e:
        error_formatted = traceback.format_exc()
        logging.error(error_formatted, extra={'exception':e})
        mail_service.notify_about_error(str(e))
        logging.debug('Exception-Handling completed. Exiting...', extra={'exception':e})
        sys.exit(-1)


# --- called at the program invocation: ---------------------
IS_DEBUG = False

if 'pydevd' in sys.modules:
    IS_DEBUG = True
    print('[RUNNING IN DEBUG-MODE!]')


if len(sys.argv) == 2:
    if sys.argv[1] == '--init':
        run_init()
    elif sys.argv[1] == '--new-token':
        run_new_token()
    else:
        print('Unrecognized argument passed!\n  Possible arguments: None, `--init`, `--new-token`')
        sys.exit(-1)
else:
    run_main()
