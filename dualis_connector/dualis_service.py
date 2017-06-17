import logging
from getpass import getpass

from bs4 import BeautifulSoup

from config_helper import ConfigHelper
from dualis_connector import login_helper
from dualis_connector.request_helper import RequestRejectedError, RequestHelper
from dualis_connector.results_handler import ResultsHandler
from version_recorder import VersionRecorder, CollectionOfChanges


class DualisService:
    def __init__(self, config_helper: ConfigHelper):
        self.config_helper = config_helper
        self.recorder = VersionRecorder('_course-results')

        self.is_state_floating = False

    def interactively_acquire_token(self) -> str:
        """
        Walks the user through executing a login into the Dualis-System to get the Token and saves it.
        @return: The Token for Dualis.
        """
        print('[The following Input is not saved, it is only used temporarily to generate a login token.]')

        token = None
        while token is None:
            dualis_username = input('Username for Dualis:   ')
            dualis_password = getpass('Password for Dualis [no output]:   ')
            try:
                token = login_helper.obtain_login_token(dualis_username, dualis_password)
            except RequestRejectedError as error:
                print('Login Failed! (%s) Please try again.' % (error))
            except (ValueError, RuntimeError) as error:
                print('Error while communicating with the Dualis System! (%s) Please try again.' % (error))

        self.config_helper.set_property('token', token)

        return token

    def _fetch_state(self) -> ({ str : BeautifulSoup}, {str : str}):
        """
        Fetches the current Result-State for the configured Dualis-Account
        @return: Tuple with (result data , course names)
        """
        token = self.get_token()

        request_helper = RequestHelper(token)
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

        result_data = { k : v[0] for k, v in results.items()}
        course_names = { k : v[1] for k, v in results.items()}
        return (result_data, course_names)

    def fetch_and_save_unchecked_state(self) -> None:
        """
        Fetches the current Result-State of the configured Dualis-Account and directly saves it, without 
         checking for changes. 
        """
        results = self._fetch_state()[0]

        self.recorder.start_new_version()
        for course_id, result_soup in results.items():
            self.recorder.save_file(course_id, result_soup.prettify())
        self.recorder.persist_new_version()

    def fetch_and_check_state(self) -> (CollectionOfChanges, {str : str}):
        """
        Fetches the current Result-State of the configured Dualis-Account and comperes it with the last known
         state for changes.
        @return: Tuple with (detected changes, course names)
        """
        logging.debug('Fetching current Dualis State...')
        results = self._fetch_state()

        logging.debug('Saving new state...')
        self.recorder.start_new_version()
        for course_id, result_soup in results[0].items():
            self.recorder.save_file(course_id, result_soup.prettify())

        logging.debug('Checking for changes...')
        changes = self.recorder.changes_of_new_version()

        self.is_state_floating = True

        return (changes, results[1])

    def save_state(self) -> None:
        """
        Persists a, until now, unsaved state. 
        """
        if not self.is_state_floating:
            raise ValueError('There is no floating state to save!')

        logging.debug('Saving new, current state as new version...')
        self.recorder.persist_new_version()
        self.is_state_floating = False

    def get_token(self) -> str:
        try:
            return self.config_helper.get_property('token')
        except ValueError:
            raise ValueError('Not yet configured!')
