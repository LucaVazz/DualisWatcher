import os
import subprocess
import shutil
from datetime import datetime
from time import strftime


class VersionRecorder:
    def __init__(self, dir_name: str):
        self.is_creating_new_version = False
        self.dir = dir_name

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            os.makedirs(os.path.join(dir_name, 'record'))
            sub_run_git(['init'])

    def start_new_version(self):
        if (self.is_creating_new_version):
            raise ValueError('A new version is already being made!')

        shutil.rmtree(os.path.join(self.dir, 'record'))
        # we also want to detect if a page was deleted

    def save_file(self, file_id, content):
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version to add files!')

        with open(os.path.join(self.dir, 'record', file_id), 'w') as f:
            f.write(content)

    def changes_of_new_version(self):
        if (not self.is_creating_new_version):
            raise ValueError('You need to start the creation of a new version and add files to detect the changes!')

        entries_raw = sub_run_git(['status', '--short', 'record/'])
        entries_raw_without_final_linebreak = entries_raw[:2]
        entries = entries_raw_without_final_linebreak.split('\n')

        added = []
        deleted = []
        changed = []

        for entry in entries:
            # an entry has the form of i.e. '?? record/asdf.txt' / ' M record/asdf.txt' / ' D record/asdf.txt'
            indicator = entry[0:2]
            file_name = entry[(3 + len('record/')):]  # because all entries are prefixed by it

            if (indicator == '??'):
                added.append(file_name)
            elif (indicator == ' D'):
                deleted.append(file_name)
            elif (indicator == ' M'):
                diff_raw = sub_run_git(['--no-pager', 'diff', '--word-diff', '--', 'record/' + file_name])
                diffs = diff_raw.split('\n@@')
                diffs = diffs[1:]  # because we don't need the preface
                changed.append((file_name, diffs))
            else:
                raise RuntimeError('Git diff reported an unexpected indicator!')

        changes_count = len(added) + len(deleted) + len(changed)
        return (changes_count, added, deleted, changed)

    def save_new_version(self):
        if (self.changes_of_new_version()[0] > 0):
            sub_run_git(['add', '.'])
            sub_run_git(['commit', '-m="new version!"', '--author="FileRecorder <>'])

        self.is_creating_new_version = False
        return


def sub_run_git(commands: []):
    commands.insert(0, 'git')
    result = subprocess.run(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    error = result.stderr.decode('utf-8')
    if (error != ''):
        raise RuntimeError(error)

    return result.stdout.decode('utf-8')
