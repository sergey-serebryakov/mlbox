import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mlbox_task', '--mlbox-task', type=str, required=True, help="Task for this MLBOX.")
    parser.add_argument('--log_dir', '--log-dir', type=str, required=False, help="Logging directory.")
    parser.add_argument('--config', type=str, required=False, help="DLBS configuration file.")
    parser.add_argument('--dlbs_cache', type=str, required=False, help="DLBS configuration file.")
    args = parser.parse_args()

    if args.mlbox_task == 'validate':
        cmd = "export PYTHONPATH=/dlbs/python; "\
              "python /dlbs/python/dlbs/experimenter.py validate --config={}".format(args.config)
        os.system(cmd)
        return

    if args.mlbox_task == 'run':
        cmd = "export PYTHONPATH=/dlbs/python DLBS_ROOT=/dlbs; "\
              "python /dlbs/python/dlbs/experimenter.py run --config={} "\
              "-Pexp.log_root_dir='\"{}\"' "\
              "-Pruntime.dlbs_cache='\"{}\"'".format(args.config, args.log_dir, args.dlbs_cache)
        print(cmd)
        os.system(cmd)
        return

    if args.mlbox_task == 'report':
        cmd = "export PYTHONPATH=/dlbs/python; "\
              "python /dlbs/python/dlbs/bench_data.py report {} --report regular".format(args.log_dir)
        print(cmd)
        os.system(cmd)
        return


if __name__ == "__main__":
    main()
