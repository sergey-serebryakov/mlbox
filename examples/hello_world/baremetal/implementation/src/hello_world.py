import argparse
import socket
from datetime import datetime


class HelloWorldMLBox(object):
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='Hello and goodbye.')

        parser.add_argument('--mlbox_task', metavar='TASK', type=str, help='the name of the task.')
        parser.add_argument('--name', metavar='NAME', type=str, help='the path to the name.')
        parser.add_argument('--greeting', metavar='FILE', type=str, help='the path to write the greeting to.')
        parser.add_argument('--farewell', metavar='FILE', type=str, help='the path to write the farewell to.')

        return parser.parse_args()

    @staticmethod
    def task_hello(args):
        # Inputs
        with open(args.name) as f:
            name = f.read().strip()
        # Outputs
        with open(args.greeting, 'w') as f:
            f.write('Hello {}, I am on {} and time is {}.\n'.format(name, socket.gethostname(), datetime.now()))

    @staticmethod
    def task_goodbye(args):
        # Inputs
        with open(args.name) as f:
            name = f.read().strip()
        with open(args.greeting) as f:
            previous_greeting = f.read().strip()
        # Outputs
        with open(args.farewell, 'w') as f:
            f.write('Previously I said: {}\n'.format(previous_greeting))
            f.write('Now I say goodbye {} from {} on {}\n'.format(name, socket.gethostname(), datetime.now()))


def main():
    args = HelloWorldMLBox.parse_args()
    if args.mlbox_task == 'hello':
        HelloWorldMLBox.task_hello(args)
    elif args.mlbox_task == 'goodbye':
        HelloWorldMLBox.task_goodbye(args)
    else:
        raise ValueError("Unsupported task: {}".format(args.mlbox_task))


if __name__ == '__main__':
    main()
