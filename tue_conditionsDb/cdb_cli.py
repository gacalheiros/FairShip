"""@package tue_conditionsDb
ConditionsDB Command Line Interface
"""
import argparse
import io
import json

from api import API
from resources.errors import errors
from models import Condition

HELP_DESC = '''


  #####  ####### ######  #     #             ####### #     #       #        
 #     # #       #     # ##    #                #    #     #      #  ###### 
 #       #       #     # # #   #                #    #     #     #   #      
 #       #####   ######  #  #  #    #####       #    #     #    #    #####  
 #       #       #   #   #   # #                #    #     #   #     #      
 #     # #       #    #  #    ##                #    #     #  #      #      
  #####  ####### #     # #     #                #     #####  #       ###### 
                                                                            
                        Conditions Database Service
                                FairSHiP 2018

Developed by Eindhoven University of Technology under GNU General Public License v3.0

Software Technology PDEng Program
Generation 2017

This script is used to retrieve condition data from a condition database.
'''


class CLI(object):
    """
    Class that implements the Command Line Interface to the tue_conditionsDb
    """

    def __init__(self):
        self.result = None
        self.is_list = False
        self.error = None

    @staticmethod
    def save(file_name, data, mode):
        """
        Save the output of the command in a file locally
        :param file_name: name of the output file
        :param data: data, in json format, to be saved into the output file
        :param mode: string that specifies in which mode the file is opened : e.g. 'w', 'a'
        """
        with io.open(file_name, mode, encoding='utf-8') as f:
            f.write(unicode(data))
            print "Data exported successfully!"

    @staticmethod
    def output(data):
        """
        Method used to convert the data to json and print it
        :param data: data to be converted and printed
        """
        parsed = json.loads(data.to_json())
        print json.dumps(parsed, indent=4, sort_keys=True)

    def produce_output(self, data, args, is_list):
        """
        Method that checks the args dictionary and based on it, calls the save or output functions.
        :param data: data to be saved or printed
        :param args: arguments given as input through the CLI
        :param is_list: boolean that is used to indicate if the data to be saved is a list
        """
        if self.error is not None:
            print self.error
        else:
            if is_list:
                for idx, s in enumerate(data):
                    if args.list_subdetectors or args.list_global_tags:
                        print idx + 1, "-", s
                    else:
                        CLI.output(s)
            else:
                CLI.output(data)

            if args.output_file:
                if args.get_snapshot or args.global_tag:
                    parsed = "["
                    for idx, x in enumerate(data):
                        parsed += json.dumps(json.loads(x.to_json()), indent=4, sort_keys=True)
                        if idx < (len(data) - 1):
                            parsed += ","
                    parsed += "]"
                    CLI.save(args.output_file, parsed, 'w')
                else:
                    final_data = json.dumps(json.loads(data.to_json()), indent=4, sort_keys=True)
                    CLI.save(args.output_file, final_data, 'w')

    @staticmethod
    def validate_arguments(args):
        """
        Method used as an extra validation step for the inputted arguments.
        :param args: arguments given as input through the CLI
        :return: True if the arguments are correct, False otherwise
        """

        list_sd_filter = [x for x in vars(args) if (x != 'list_subdetectors' and vars(args)[x] is not None)]

        flag_ls = len(list_sd_filter) > 2 and args.list_subdetectors is True  # fixme: hardcoded value

        show_cd_filter = [x for x in vars(args) if
                          (x != 'condition' and vars(args)[x] is not None and vars(args)[x] is not False)]

        flag_cd = len(show_cd_filter) == 0 and args.condition is not None

        add_sub_filter = [x for x in vars(args) if
                          (x != 'new_sub' and vars(args)[x] is not None and vars(args)[x] is not False)]

        flag_add_sub = len(add_sub_filter) != 0 and args.new_sub is not None

        output_file_filter = [x for x in vars(args) if
                              (x != 'output_file' and vars(args)[x] is not None and vars(args)[x] is not False)]

        flag_f = len(output_file_filter) == 0 and args.output_file is not None

        if flag_ls or flag_cd or flag_add_sub or flag_f:
            return True

        return False

    def run(self, *params):
        """
        Main function of the CLI which receives arguments from the terminal (or from the tests), validates them, and
        then calls the corresponding API method to contact the db and receive the result. If the correct arguments are
        given, the result can be outputted as a file or through the terminal.

        :param params: Parameters given to the function. Used for automated unittests, where there is no input from the
        terminal, so arguments are passed to this variable.
        :return: The result that is produced when executing the corresponding commands. The result is one of the python
        objects (or a list of objects) defined in the models.py, which correspond to database entities.
        """

        api = API()

        parser = argparse.ArgumentParser(description=HELP_DESC, formatter_class=argparse.RawDescriptionHelpFormatter)

        # mutually exclusive group for list subdetectors, show subdetector and add subdetector

        group_lsn = parser.add_mutually_exclusive_group()

        # mutually exclusive group for show condition

        group_ci = parser.add_mutually_exclusive_group()

        group_lsn.add_argument('-ls', '--list-subdetectors',
                               dest='list_subdetectors',
                               help='Lists all Subdetectors from the Conditions database.',
                               action="store_true")

        group_lsn.add_argument('-gas', '--get-all-subdetectors',
                               dest='get_all_subdetectors',
                               help='Gets all Subdetectors from the Conditions database.',
                               action="store_true")

        group_lsn.add_argument('-ss', '--show-subdetector',
                               dest='subdetector',
                               default=None,
                               required=False,
                               help='Shows all the data related to a specific Subdetector.')

        group_lsn.add_argument('-as', '--add-subdetector',
                               dest='new_sub',
                               default=None,
                               required=False,
                               help='Adds a new Subdetector and its Conditions from a path to a JSON file.')

        group_lsn.add_argument('-gs', '--get-snapshot',
                               dest='get_snapshot',
                               default=None,
                               required=False,
                               help='Gets a snapshot of Conditions based on a specific date.')

        group_ci.add_argument('-lg', '--list-global-tags',
                              dest='list_global_tags',
                              help='Lists all Global Tags from the Conditions database.',
                              action="store_true")

        group_ci.add_argument('-sc', '--show-condition',
                              dest='condition',
                              default=None,
                              required=False,
                              help='Shows a specific Condition of a Subdetector. Search is done by Condition name.')

        group_ci.add_argument('-gt', '--global-tag',
                              dest='global_tag',
                              default=None,
                              required=False,
                              help='Creates a new global tag based on the retrieved snapshot. If used alone retrieves all conditions globally tagged under the passed argument.')

        group_ci.add_argument('-st', '--show-tag',
                              dest='tag',
                              default=None,
                              required=False,
                              help='Retrieves a list of Conditions based on a specific tag.')

        parser.add_argument('-f', '--file',
                            dest='output_file',
                            default=None,
                            required=False,
                            help='Redirects the output of a command to a JSON file. This command must have a return \
                            value and not only print data to the standard output')

        # Tweak used to test the CLI through unittests, without requesting input from the terminal.
        if params:
            args = parser.parse_args(params)
        else:
            args = parser.parse_args()

        #         print vars(args)

        if self.validate_arguments(args):
            parser.error('arguments error')

        if args.list_subdetectors is True:
            print "-ls executed"
            subdetectors_names = api.list_subdetectors()
            self.result = subdetectors_names
            self.is_list = True

        if args.get_all_subdetectors is True:
            print "-gas executed"
            subdetectors = api.get_all_subdetectors()
            self.result = subdetectors
            self.is_list = True

        if args.subdetector is not None and args.condition is None and args.tag is None:
            print "-ss executed"
            subdetector = api.show_subdetector(args.subdetector)
            if subdetector is None:
                self.error = "error " + errors.keys()[0] + ": " + errors["0001"]
            self.result = subdetector

        if args.new_sub is not None:
            print "-as executed"
            with open(args.new_sub) as loaded_file:
                data = json.load(loaded_file)
                added = api.add_subdetector(data)
                if added == 1:
                    print "Subdetector added successfully!"
                    return True
                print "Error adding new Subdetector"
                return False

        if args.get_snapshot is not None:
            print "-gs executed"
            snapshot = api.get_snapshot(args.get_snapshot, args.global_tag)
            self.result = snapshot
            self.is_list = True

        if args.list_global_tags is True:
            print "-lg executed"
            global_tags_names = api.list_global_tags()
            self.result = global_tags_names
            self.is_list = True

        if args.subdetector is not None and args.condition is not None:
            print "-sc executed"
            condition = api.show_subdetector_condition(args.subdetector, args.condition)
            if condition is None:
                self.error = "error " + errors.keys()[1] + ": " + errors["0002"]
            self.result = condition

        if args.global_tag is not None and args.get_snapshot is None:
            print "-gt executed"
            conditions_by_tag = api.get_data_global_tag(args.global_tag)
            self.result = conditions_by_tag
            self.is_list = True

        if args.tag is not None:
            print "-st executed"
            condition = api.show_subdetector_tag(args.subdetector, args.tag)
            if not isinstance(condition, Condition):
                self.is_list = True
            if condition is None:
                self.error = "error " + errors.keys()[2] + ": " + errors["0003"]
            self.result = condition

        self.produce_output(self.result, args, self.is_list)

        return self.result


if __name__ == '__main__':
    service = CLI()
    service.run()
