import os
import subprocess

class CollectionOfChanges:
    def __init__(self, count: int, added: [str], deleted: {str : str}, modified: {str : [str]}):
        self.diff_count = count
        self.added = added
        self.deleted = deleted
        self.modified = modified


class VersionRecorder:
    """
    Saves the states at different points in time as versions and provides utilities to detect changes
    in the current state against the previous.
    """
    def __init__(self, dir_name: str):
        self.is_creating_new_version = False
        self.dir = dir_name

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            os.chdir(dir_name)
            try:
                self._sub_run_git(['init'])
                self._sub_run_git(['config', 'user.name', '"FileRecorder"'])
                self._sub_run_git(['config', 'user.email', '"no-reply@localhost"'])
            finally:
                os.chdir('..')

    def start_new_version(self):
        if (self.is_creating_new_version):
            raise ValueError('A new version is already being created!')

        # We also want to detect if a page was deleted, so we delete all existing files
        #  this way, when all currently present pages were saved, git notices that a file is missing
        for file_name in os.listdir(self.dir):
            file_path = os.path.join(self.dir, file_name)
            if os.path.isfile(file_path):  # i.e. ignore sub-directories (including .git)
                os.remove(file_path)

        self.is_creating_new_version = True

    def save_file(self, file_id: str, content: str):
        if (not self.is_creating_new_version):
            raise ValueError(
                'You need to start the creation of a new version to add files!'
            )

        file_path = os.path.join(self.dir, file_id)

        with open(file_path, encoding='utf-8', errors='backslashreplace', mode='w+') as f:
            f.write(content)

    def changes_of_new_version(self) -> CollectionOfChanges:
        if (not self.is_creating_new_version):
            raise ValueError(
                'You need to start the creation of a new version and add files to detect changes!'
            )

        os.chdir(self.dir)
        try:
            entries_raw = self._sub_run_git(['status', '--short'])

            if (entries_raw == ''):
                return CollectionOfChanges(0, [], [], {})

            entries_raw_without_final_linebreak = entries_raw[:-1]
            entries = entries_raw_without_final_linebreak.split('\n')

            added = []
            deleted = {}
            modified = {}

            for entry in entries:
                # An entry has the form of i.e. '?? asdf.txt' / ' M asdf.txt' / ' D asdf.txt'
                #  (the 'AD' and 'AM' variants indicate that these files were added in a previous
                #  run but not yet persisted as a new version)
                indicator = entry[0:2]
                file_name = entry[3:]

                if (indicator == '??' or indicator == 'A '):
                    added.append(file_name)
                elif (indicator == ' D' or indicator == 'AD' or indicator == 'D '):
                    old_raw = self._sub_run_git(
                        ['--no-pager', 'diff', '--word-diff', '--', file_name]
                    )
                    old_without_diff_marks = old_raw.replace('[-', '').replace('-]', '')
                    old = old_without_diff_marks.split('@@\n')
                    old = old[1]  # because we don't need the preface
                    deleted.update( {file_name : old} )
                elif (indicator == ' M' or indicator == 'AM' or indicator == 'M '):
                    diff_raw = self._sub_run_git(
                        ['--no-pager', 'diff', '--word-diff', '--', file_name]
                    )
                    diffs = diff_raw.split('\n@@')
                    diffs = diffs[1:]  # because we don't need the preface
                    formatted_diffs = []
                    for diff in diffs:
                        diff = diff.replace('\r\n', '\n')
                        diff_lines = diff.split('\n')
                        diff_lines[0] = '[...]\n'
                        formatted_diffs.append('\n'.join(diff_lines))
                    formatted_diffs.append('\n[...]')
                    modified.update( {file_name : formatted_diffs} )
                else:
                    raise RuntimeError(
                        'Git diff reported an unexpected indicator (%s)!'%(indicator)
                    )

            changes_count = len(added) + len(deleted) + len(modified)
        finally:
            os.chdir('..')

        return CollectionOfChanges(changes_count, added, deleted, modified)


    def persist_new_version(self):
        if (self.changes_of_new_version().diff_count > 0):
            os.chdir(self.dir)
            try:
                self._sub_run_git(['add', '.'])
                self._sub_run_git(['commit', '-m "new version!"'])
            finally:
                os.chdir('..')

        self.is_creating_new_version = False

    @staticmethod
    def _sub_run_git(commands: []) -> str:
        commands.insert(0, 'git')
        result = subprocess.run(
            commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=(os.name == 'nt')  # True if the program runs on Windows, otherwise False
        )

        error_message = result.stderr.decode('utf-8', 'backslashreplace')
        if (error_message != ''):
            raise RuntimeError(error_message)

        return result.stdout.decode('utf-8', 'backslashreplace')
