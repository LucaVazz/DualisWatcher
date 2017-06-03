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
                sub_run_git(['init'])
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

    def save_file(self, file_id, content):
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version to add files!')

        with open(os.path.join(self.dir, file_id), 'w+') as f:
            f.write(content)

    def changes_of_new_version(self):
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version and add files to detect the changes!')

        os.chdir(self.dir)
        try:
            entries_raw = sub_run_git(['status', '--short'])
            entries_raw_without_final_linebreak = entries_raw[:-1]
            entries = entries_raw_without_final_linebreak.split('\n')

            added = []
            deleted = []
            changed = []

            for entry in entries:
                # an entry has the form of i.e. '?? asdf.txt' / ' M asdf.txt' / ' D asdf.txt'
                indicator = entry[0:2]
                file_name = entry[3:]

                if (indicator == '??'):
                    added.append(file_name)
                elif (indicator == ' D'):
                    deleted.append(file_name)
                elif (indicator == ' M'):
                    diff_raw = sub_run_git(['--no-pager', 'diff', '--word-diff', '--', file_name])
                    diffs = diff_raw.split('\n@@')
                    diffs = diffs[1:]  # because we don't need the preface
                    changed.append((file_name, diffs))
                else:
                    raise RuntimeError('Git diff reported an unexpected indicator!')

            changes_count = len(added) + len(deleted) + len(changed)
        finally:
            os.chdir('..')

        return (changes_count, added, deleted, changed)


    def save_new_version(self):
        if (self.changes_of_new_version()[0] > 0):
            os.chdir(self.dir)
            try:
                sub_run_git(['add', '.'])
                sub_run_git(['commit', '-m "new version!"', '--author="FileRecorder<no-reply@localhost>"'])
            finally:
                os.chdir('..')

        self.is_creating_new_version = False
        return


def sub_run_git(commands: []):
    commands.insert(0, 'git')
    result = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    error = result.stderr.decode('utf-8')
    if (error != ''):
        raise RuntimeError(error)

    return result.stdout.decode('ISO-8859-1')
