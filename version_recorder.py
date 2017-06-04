import os
import subprocess


class VersionRecorder:
    def __init__(self, dir_name: str):
        self.is_creating_new_version = False
        self.dir = dir_name

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            os.chdir(dir_name)
            try:
                self._sub_run_git(['init'])
            finally:
                os.chdir('..')

    def start_new_version(self):
        if (self.is_creating_new_version):
            raise ValueError('A new version is already being made!')

        # we also want to detect if a page was deleted, so we delete all existing files
        for file in os.listdir(self.dir):
            file_path = os.path.join(self.dir, file)
            if os.path.isfile(file_path):  # i.e. ignore .git and other directories
                os.remove(file_path)

        self.is_creating_new_version = True

    def save_file(self, file_id: str, content: str):
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version to add files!')

        with open(os.path.join(self.dir, file_id), 'w+') as f:
            f.write(content)

    def changes_of_new_version(self) -> 'CollectionOfDiffIds':
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version and add files to detect the changes!')

        os.chdir(self.dir)
        try:
            entries_raw = self._sub_run_git(['status', '--short'])

            if (entries_raw == ''):
                return CollectionOfDiffIds(0, [], [], {})

            entries_raw_without_final_linebreak = entries_raw[:-1]
            entries = entries_raw_without_final_linebreak.split('\n')

            added = []
            deleted = []
            modified = {}

            for entry in entries:
                # an entry has the form of i.e. '?? asdf.txt' / ' M asdf.txt' / ' D asdf.txt'
                indicator = entry[0:2]
                file_name = entry[3:]

                if (indicator == '??'):
                    added.append(file_name)
                elif (indicator == ' D'):
                    deleted.append(file_name)
                elif (indicator == ' M'):
                    diff_raw = self._sub_run_git(['--no-pager', 'diff', '--word-diff', '--', file_name])
                    diffs = diff_raw.split('\n@@')
                    diffs = diffs[1:]  # because we don't need the preface
                    modified.update( {file_name : diffs} )
                else:
                    raise RuntimeError('Git diff reported an unexpected indicator!')

            changes_count = len(added) + len(deleted) + len(modified)
        finally:
            os.chdir('..')

        return CollectionOfDiffIds(changes_count, added, deleted, modified)


    def save_new_version(self):
        if (self.changes_of_new_version().diff_count > 0):
            os.chdir(self.dir)
            try:
                self._sub_run_git(['add', '.'])
                self._sub_run_git(['commit', '-m "new version!"', '--author="FileRecorder<no-reply@localhost>"'])
            finally:
                os.chdir('..')

        self.is_creating_new_version = False

    @staticmethod
    def _sub_run_git(commands: []) -> str:
        commands.insert(0, 'git')
        result = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        error = result.stderr.decode('utf-8')
        if (error != ''):
            raise RuntimeError(error)

        return result.stdout.decode('ISO-8859-1')


class CollectionOfDiffIds:
    def __init__(self, count: int, added: [str], deleted: [str], modified: {str : str}):
        self.diff_count = count
        self.added = added
        self.deleted = deleted
        self.modified = modified
