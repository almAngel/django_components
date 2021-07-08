from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os
from string import Template

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

            generated = True

            if components:
                
                for comp in components:
                    comp_path_array = str(comp).split('/')
                    comp_name = str(comp_path_array[-1])
                    class_comp_name = ''.join(
                        s.capitalize() for s in comp_name.split('_')
                    ) if '_' in comp_name else comp_name.capitalize() 

                    extensions = ['css', 'html', 'js', 'py']

                    path =  f'{settings.BASE_DIR}/{"/".join(comp_path_array)}/'

                    Path(path).mkdir(parents=True, exist_ok=True)

                    templ_replacement = {
                        'name': comp_name,
                        'class_name': class_comp_name
                    }

                    for ext in extensions:
                        
                        filepath = path + comp_name + '.' + ext
                        templpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', f'../gentemplates/{ext}.templ'))

                        if not os.path.exists(filepath):
                            with open(templpath, 'r') as templ_file, open(filepath, 'w') as out_file:
                                source = Template(templ_file.read())
                                filled_templ = source.substitute(templ_replacement)
                                out_file.write(filled_templ)
                        else:
                            generated = False
                            
                    if generated:
                        self.stdout.write(f'>> Component {comp_name} generated in {"/".join(comp_path_array)}/')
                    else:
                        self.stdout.write(f'>> Component {comp_name} already exists.')