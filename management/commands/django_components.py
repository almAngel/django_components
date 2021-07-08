from django.core.management.base import BaseCommand
import os
from django.conf import settings

class Command(BaseCommand):
    help = '>> Django Components manager. This tool is used to maintain django_components projects.'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--initialize', action='store_true', help='Set up Django Components')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate elements')
        parser.add_argument('-c', '--component', nargs='+', type=str, help='Select component as element to operate with')

    def handle(self, *args, **kwargs):
        initialize = kwargs['initialize']
        generate = kwargs['generate']
        components = kwargs['component']

        if initialize:
            self.stdout.write('>> Creating component.py file and adding it to your project...')

            path =  settings.BASE_DIR / \
                    str(settings.BASE_DIR).split('/')[len(str(settings.BASE_DIR).split('/'))-1] / \
                    'components.py'

            if not os.path.exists(path):
                with open(path, 'w'): pass
            else:
                self.stdout.write('>> Components file already initialized.')

        elif generate:

            if components:
                for comp in components:
                    comp_path_array = str(comp).split('/')
                    comp_name = comp_path_array[-1]

                    self.stdout.write(f'>> Component {comp_name} generated in {"/".join(comp_path_array[:-1])}')