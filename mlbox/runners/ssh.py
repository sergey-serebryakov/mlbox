from os import path
from typing import List, Union

from mlbox.mlbox_local_run import run_or_die
from mlbox.runners.lib.runner import MLBoxRunner


class SSHRunner(MLBoxRunner):
    """ """

    def __init__(self, config: dict):
        """
        Mandatory key: host, user, runtime. mlbox
        """
        super(SSHRunner, self).__init__(config)

    def configure(self):
        """ """
        conn = "{}@{}".format(self.config['user'], self.config['host'])
        if self.config['runtime']['sync'] is True:
            local_dir = path.abspath(path.dirname(__name__))
            remote_dir = self.config['runtime']['remote_dir']
            run_or_die("ssh -o StrictHostKeyChecking=no {} 'mkdir -p {}'".format(conn, remote_dir))
            for d in ('mlbox', 'platforms'):
                run_or_die("rsync -r {}/{} {}:{}".format(local_dir, d, conn, remote_dir))

        if self.config['mlbox']['sync'] is True:
            local_dir = path.abspath(self.config['mlbox_path'])
            remote_dir = path.dirname(self.config['mlbox']['remote_dir'])
            run_or_die("ssh -o StrictHostKeyChecking=no {} 'mkdir -p {}'".format(conn, remote_dir))
            run_or_die("rsync -r {} {}:{}".format(local_dir, conn, remote_dir))

        mlbox_cmd = "python -m mlbox.runners.simple_runner configure ./platforms/platforms.yaml:{} {}".format(
            self.config['remote_local'], self.config['mlbox']['remote_dir']
        )
        cmd = "ssh -o StrictHostKeyChecking=no {} PYTHONPATH={} 'cd {}; {}'".format(
            conn, self.config['runtime']['remote_dir'], self.config['runtime']['remote_dir'], mlbox_cmd
        )
        run_or_die(cmd)

    def execute(self, cmd: Union[List[str], str]) -> int:
        """ Execute command `cmd` on a remote platform specified by `platform_config`.
        Args:
            cmd (List[str]): Command to execute. It is built with assumptions that it will run locally on the
                specific platform described by `platform_config`.

        ssh -o StrictHostKeyChecking=no ${USER}@${NODE} -p ${PORT} "command"
        Standard SSH port is 22
        """
        conn = "{}@{}".format(self.config['user'], self.config['host'])

        mlbox_cmd = "python -m mlbox.runners.simple_runner run ./platforms/platforms.yaml:{} {}:{}/{}".format(
            self.config['remote_local'], self.config['mlbox']['remote_dir'], self.config['remote_task'],
            self.config['remote_input_group']
        )
        cmd = "ssh -o StrictHostKeyChecking=no {} PYTHONPATH={} 'cd {}; {}'".format(
            conn, self.config['runtime']['remote_dir'], self.config['runtime']['remote_dir'], mlbox_cmd
        )
        run_or_die(cmd)

        local_dir = path.dirname(path.abspath(self.config['mlbox_path']))
        remote_dir = self.config['mlbox']['remote_dir']
        run_or_die("rsync -r {}:{} {}".format(conn, remote_dir, local_dir))
        return 0
