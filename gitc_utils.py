#
# Copyright (C) 2015 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import os
import sys

import git_command
import git_config


# TODO (sbasi) - Remove this constant and fetch manifest dir from /gitc/.config
GITC_MANIFEST_DIR = '/usr/local/google/gitc/'
GITC_FS_ROOT_DIR = '/gitc/manifest-rw/'
NUM_BATCH_RETRIEVE_REVISIONID = 300

def _set_project_revisions(projects):
  """Sets the revisionExpr for a list of projects.

  Because of the limit of open file descriptors allowed, length of projects
  should not be overly large. Recommend calling this function multiple times
  with each call not exceeding NUM_BATCH_RETRIEVE_REVISIONID projects.

  @param projects: List of project objects to set the revionExpr for.
  """
  # Retrieve the commit id for each project based off of it's current
  # revisionExpr and it is not already a commit id.
  project_gitcmds = [(
      project, git_command.GitCommand(None,
                                      ['ls-remote',
                                       project.remote.url,
                                       project.revisionExpr],
                                      capture_stdout=True, cwd='/tmp'))
      for project in projects if not git_config.IsId(project.revisionExpr)]
  for proj, gitcmd in project_gitcmds:
    if gitcmd.Wait():
      print('FATAL: Failed to retrieve revisionExpr for %s' % proj)
      sys.exit(1)
    proj.revisionExpr = gitcmd.stdout.split('\t')[0]

def generate_gitc_manifest(client_dir, manifest):
  """Generate a manifest for shafsd to use for this GITC client.

  @param client_dir: GITC client directory to install the .manifest file in.
  @param manifest: XmlManifest object representing the repo manifest.
  """
  print('Generating GITC Manifest by fetching revision SHAs for each '
        'project.')
  index = 0
  while index < len(manifest.projects):
    _set_project_revisions(
        manifest.projects[index:(index+NUM_BATCH_RETRIEVE_REVISIONID)])
    index += NUM_BATCH_RETRIEVE_REVISIONID
  # Save the manifest.
  with open(os.path.join(client_dir, '.manifest'), 'w') as f:
    manifest.Save(f)
