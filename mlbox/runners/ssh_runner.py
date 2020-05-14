import copy
import logging
from os import path
from typing import List, Union
from mlbox import metadata
from mlbox.runners.mlbox_runner import MLBoxRunner
from mlbox.util import Utils


logger = logging.getLogger(__name__)


class SSHRunner(MLBoxRunner):
    """ """

    def __init__(self, mlbox: metadata.MLBox, platform_config: dict):
        """
        Mandatory key: host, user, runtime. mlbox
        """
        # TODO: refactor and fix this
        super(SSHRunner, self).__init__({})
        self.mlbox: metadata.MLBox = mlbox
        self.platform_config: dict = copy.deepcopy(platform_config)
        #
        if self.platform_config.get('runtime', None) is None:
            self.platform_config['runtime'] = {'remote_dir': None, 'sync': True}
        if self.platform_config['runtime'].get('remote_dir', None) is None:
            self.platform_config['runtime']['remote_dir'] = '.mlbox'
        logger.info('SSHRunner: remote runtime = %s', str(self.platform_config['runtime']))
        #
        if self.platform_config.get('mlbox', None) is None:
            self.platform_config['mlbox'] = {'remote_dir': None, 'sync': True}
        if self.platform_config['mlbox'].get('remote_dir', None) is None:
            self.platform_config['mlbox']['remote_dir'] = path.join(
                self.platform_config['runtime']['remote_dir'],
                'mlboxes',
                mlbox.name,
                mlbox.implementation_type
            )
        logger.info('SSHRunner: remote mlbox = %s', str(self.platform_config['mlbox']))

    def configure(self):
        """ """
        platform: dict = self.platform_config
        conn = "{}@{}".format(platform['user'], platform['host'])

        # Sync mlbox root directory with the remote host. We only need two sub-directories - mlbox/ and platforms/.
        if platform['runtime']['sync'] is True:
            #                  dirname    dirname  dirname
            # ssh_runner.py -> runners -> mlbox -> mlbox_root
            local_dir = path.abspath(path.dirname(path.dirname(path.dirname(__file__))))
            remote_dir = platform['runtime']['remote_dir']
            Utils.run_or_die("ssh -o StrictHostKeyChecking=no {} 'mkdir -p {}'".format(conn, remote_dir))
            for d in ('mlbox', 'platforms'):
                Utils.run_or_die("rsync -r {}/{} {}:{}".format(local_dir, d, conn, remote_dir))

        # Sync MLBox directories
        if platform['mlbox']['sync'] is True:
            # The 'local_dir' and 'remote_dir' must both be directories.
            local_dir, remote_dir = self.mlbox.path, platform['mlbox']['remote_dir']
            Utils.run_or_die("ssh -o StrictHostKeyChecking=no {} 'mkdir -p {}'".format(conn, remote_dir))
            Utils.run_or_die("rsync -r {}/ {}:{}/".format(local_dir, conn, remote_dir))

        # Build a command to run on a remote server to configure MLBox on a remote host. This is a simplified version,
        # assuming the remote host is the one that will run MLBox, so no need to specify platform configuration file.
        # mlbox_cmd = "python -m mlbox configure ./platforms/platforms.yaml:{} {}".format(
        #     self.config['remote_local'], platform['mlbox']['remote_dir']
        # )
        # TODO: we need python3.6 here. Better solution?
        mlbox_path = path.relpath(platform['mlbox']['remote_dir'], platform['runtime']['remote_dir'])
        mlbox_cmd = "python3.6 -m mlbox configure {}".format(mlbox_path)
        cmd = "ssh -o StrictHostKeyChecking=no {} PYTHONPATH={} 'cd {}; {}'".format(
            conn, platform['runtime']['remote_dir'], platform['runtime']['remote_dir'], mlbox_cmd
        )
        Utils.run_or_die(cmd)

    def execute(self, cmd: Union[List[str], str]) -> int:
        """ Execute command `cmd` on a remote platform specified by `platform_config`.
        Args:
            cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
                specific platform described by `platform_config`.

        ssh -o StrictHostKeyChecking=no ${USER}@${NODE} -p ${PORT} "command"
        Standard SSH port is 22
        """
        platform: dict = self.platform_config
        conn = "{}@{}".format(platform['user'], platform['host'])

        # mlbox_cmd = "python3.6 -m mlbox run ./platforms/platforms.yaml:{} {}:{}/{}".format(
        #     self.config['remote_local'], self.config['mlbox']['remote_dir'], self.config['remote_task'],
        #     self.config['remote_input_group']
        # )
        # mlbox_path:task/defaults
        task: dict = self.mlbox.implementation.task
        mlbox_path = path.relpath(platform['mlbox']['remote_dir'], platform['runtime']['remote_dir'])
        mlbox_cmd = "python3.6 -m mlbox run {}:{}/{}".format(
            mlbox_path, task['name'], task['input_group']
        )
        cmd = "ssh -o StrictHostKeyChecking=no {} PYTHONPATH={} 'cd {}; {}'".format(
            conn, platform['runtime']['remote_dir'], platform['runtime']['remote_dir'], mlbox_cmd
        )
        Utils.run_or_die(cmd)

        # Sync back results
        # TODO: Only workspace/ directory is synced. Better solution?
        remote_dir, local_dir = platform['mlbox']['remote_dir'], self.mlbox.path
        Utils.run_or_die("rsync -r {}:{}/workspace/ {}/workspace/".format(conn, remote_dir, local_dir))
        return 0
