class Help(object):
    @staticmethod
    def generic_help_message():
        msg = "usage: mlbox <command> [<args>]\n\n"\
              "These are common MLBox commands:\n\n"\
              "mlbox help\n"\
              "\thelp         Show list of supported commands, get help for a particular command\n\n"\
              "mlbox execution\n"\
              "\tconfigure    Configure MLBox\n"\
              "\trun          Run MLBox\n\n" \
              "mlbox information\n" \
              "\tdescribe     Briefly describe MLBox configuration\n\n" \
              "See 'python -m mlbox help <command>' to read about specific command\n"
        print(msg)

    @staticmethod
    def help(args: list):
        if len(args) != 1:
            msg = "usage: mlbox help <command>\n"\
                  "where:\n"\
                  "\t<command>  A specific command such as 'configure', 'run', 'describe' etc.\n"
        elif args[0] == 'run':
            msg = Help.help_for_run()
        elif args[0] == 'configure':
            msg = Help.help_for_configure()
        elif args[0] == 'describe':
            msg = Help.help_for_describe()
        else:
            msg = "\nunknown command: {}\n".format(args[0])
        print(msg)

    @staticmethod
    def help_for_run() -> str:
        msg = "usage: mlbox run [PLATFORM_FILE[:RUNNER]] MLBOX_PATH[:TASK[/PARAM_SET]]\n"\
              "where:\n"\
              "\tPLATFORM_FILE   YAML file                 Platform configuration file\n"\
              "\tRUNNER          MLBox runner ID           Runner to run MLBox\n"\
              "\tMLBOX_PATH      Path to MLBox             Path to a MLBox directory\n"\
              "\tTASK            MLBox task to run         Run one of the tasks supported by MLBox\n"\
              "\tPARAM_SET       Default parameter values  Use this set of task's default parameters\n"
        return msg

    @staticmethod
    def help_for_configure() -> str:
        msg = "usage: mlbox configure [PLATFORM_FILE[:RUNNER]] MLBOX_PATH\n"\
              "where:\n" \
              "\tPLATFORM_FILE   YAML file                 Platform configuration file.\n" \
              "\tRUNNER          MLBox runner ID           Runner to run MLBox\n" \
              "\tMLBOX_PATH      Path to MLBox             Path to a MLBox directory\n"
        return msg

    @staticmethod
    def help_for_describe() -> str:
        msg = "usage: mlbox describe MLBOX_PATH\n"\
              "where:\n"\
              "\tMLBOX_PATH      Path to MLBox             Path to a MLBox directory\n"
        return msg
