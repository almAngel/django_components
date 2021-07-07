from django.core.management.base import BaseCommand
import os
from django.conf import settings

class Command(BaseCommand):
    help = '>> Django Components manager. This tool is used to maintain django_components projects.'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--initialize', action='store_true', help='Set up Django Components')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate elements')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate elements')

    def handle(self, *args, **kwargs):
        initialize = kwargs['initialize']
        generate = kwargs['generate']

        if initialize:
            self.stdout.write('>> Creating component.py file and adding it to your project...')

            path =  settings.BASE_DIR / \
                    str(settings.BASE_DIR).split('/')[len(str(settings.BASE_DIR).split('/'))-1] / \
                    'components.py'

            if not os.path.exists(path):
                with open(path, 'w'): pass
            else:
                self.stdout.write('>> Components file already initialized.')