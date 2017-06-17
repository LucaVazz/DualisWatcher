import logging
from http.client import HTTPConnection

from config_helper import ConfigHelper
from version_recorder import VersionRecorder


class ScheduleService:
    def __init__(self, config_helper: ConfigHelper):
        self.config_helper = config_helper
        try:
            self.uid = self.config_helper.get_property('schedule')['uid']
            self.is_activated = True
        except ValueError:
            self.uid = None
            self.is_activated = False

        self.recorder = VersionRecorder('_schedule')
        self.is_state_floating = False

    def interactively_configure(self) -> bool:
        """
        Walks the user through configuring the watcher for a DHBW Mannheim Schedule, if they want to 
        activate it.
        @return: If the user selected to activate the schedule watcher. 
        """
        do_config_input = input(
            'Do you want to activate a Watcher for a DHBW Mannheim Course-Schedule [y/n]?   '
        )
        while not (do_config_input == 'y' or do_config_input == 'n'):
            do_config_input = input('Unrecognized input. Try again:   ')

        if do_config_input == 'n':
            self.is_activated = False
            self.config_helper.remove_property('schedule')
        else:
            print(
                  'Go to `http://vorlesungsplan.dhbw-mannheim.de/ical.php` and select your course.'
                + '\nYou will be presented with a link ending in `?uid=`, what follows after that is the UID.'
            )
            is_config_valid = False
            while not is_config_valid:
                uid = input('Paste the displayed UID here:   ')

                print('Testing given UID...')
                try:
                    result = self._fetch_state(uid)
                except BaseException as e:
                    print(
                        'Error at trying to access the schedule with the given UID (%s)! Please try again.'%(
                            str(e)
                        )
                    )
                else:
                    self.uid = uid
                    is_config_valid = True

            self.config_helper.set_property('schedule', {'uid': self.uid})

            self.is_activated = True

        return self.is_activated

    def _fetch_state(self, uid) -> str:
        connection = HTTPConnection('vorlesungsplan.dhbw-mannheim.de')
        connection.request(
            'GET',
            '/ical.php?uid=%s'%(uid)
        )
        response = connection.getresponse()

        response_status = response.getcode()
        if response_status != 200:
            raise RuntimeError('Server reported Status %s'%(response_status))

        return response.read().decode('utf-8')

    def fetch_and_save_unchecked_state(self) -> None:
        """
        Fetches the current state and directly saves it, without comparison with a previous state.
        """
        if not self.is_activated:
            raise ValueError('Not activated and configured!')

        schedule = self._fetch_state(self.uid)

        self.recorder.start_new_version()
        self.recorder.save_file('schedule.ical', schedule)
        self.recorder.persist_new_version()

    def fetch_and_check_state(self) -> [str]:
        """
        Fetches the current state of the schedule and compares it to the previous.
        @return: A list of differences to the last known state.
        """
        if not self.is_activated:
            raise ValueError('Not activated and configured!')

        logging.debug('Fetching current Schedule...')
        schedule = self._fetch_state(self.uid)

        logging.debug('Saving new state...')
        self.recorder.start_new_version()
        self.recorder.save_file('schedule.ical', schedule)

        logging.debug('Checking for changes...')
        changes = self.recorder.changes_of_new_version()

        self.is_state_floating = True

        if changes.diff_count > 0:
            if 'schedule.ical' in changes.modified:
                return changes.modified['schedule.ical']
            else:
                raise ValueError('Unexpected state!')
        else:
            return []

    def save_state(self) -> None:
        """
        Persists a, until now, unsaved state. 
        """
        if not self.is_state_floating:
            raise ValueError('There is no floating state to save!')

        logging.debug('Saving new, current state as new version...')
        self.recorder.persist_new_version()
        self.is_state_floating = False
