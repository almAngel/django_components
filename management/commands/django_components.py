from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os, sys
import inspect, importlib as implib
from string import Template

class Command(BaseCommand):
    help = '>> Django Components manager. This tool is used to maintain django_components projects.'

    root = settings.BASE_DIR
    appname = str(settings.BASE_DIR).split('/')[-1]
    root_app = root / appname
    components_base = ''

    def add_arguments(self, parser):
        parser.add_argument('-i', '--initialize', type=str, help='Set up Django Components')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate elements')
        parser.add_argument('-c', '--component', nargs='+', type=str, help='Select component as element to operate with')

    def handle(self, *args, **kwargs):
        initialize = kwargs['initialize']
        generate = kwargs['generate']
        components = kwargs['component']

        if initialize:

            componentsfile_path = self.root_app / 'components.py'
            settings_path = str(self.root_app / 'settings.py')
            self.components_base = initialize
            self.components_parent = self.components_base.split('/')[0]

            if not os.path.exists(componentsfile_path):
                self.stdout.write('>> Creating component.py file and adding it to your project...')

                # ADD IMPORT OS
                lines = []
                with open(settings_path, 'r+') as settings_file:
                    lines = settings_file.readlines()
                    for i, l in enumerate(lines):
                        if 'import' in l:
                            if 'os' not in sys.modules['componentes.settings'].__dir__():
                                lines.insert(i + 1, 'import os\n')
                                settings_file.close()
                                break
                        
                with open(settings_path, 'w') as settings_file:
                    lines = "".join(lines)
                    settings_file.write(lines)
                    settings_file.close()

                # ADD COMPONENTS BLOCK
                lines = []
                with open(componentsfile_path, 'w'), open(settings_path, 'r+') as settings_file: 
                    if not hasattr(settings, 'COMPONENTS'):
                        lines = settings_file.readlines()

                        for i, l in enumerate(lines):

                            if 'BASE_DIR' in l:
                                lines.insert(
                                    i + 2, 
                                    (
                                    '\n# DJANGO_COMPONENTS PLUGIN\n'
                                    'COMPONENTS = {\n'
                                        '\t\'libraries\': [\n'
                                            f'\t\t\'{self.appname}.components\'\n'
                                        '\t]\n'
                                    '}\n'
                                    'COMPONENTS_BASE = ' + f'f\'{{BASE_DIR}}/{self.components_base}\''
                                    '\nCOMPONENTS_DIRS = [ dir for dir in os.listdir(COMPONENTS_BASE) if os.path.isdir(os.path.join(COMPONENTS_BASE, dir)) ]\n'
                                    )
                                )
                                break
                    settings_file.close()
                with open(settings_path, 'w') as settings_file:
                    lines = "".join(lines)
                    settings_file.write(lines)
                    settings_file.close()
                
                # # ADD TEMPLATE DIRS
                # lines = []
                # with open(componentsfile_path, 'w'), open(settings_path, 'r+') as settings_file: 
                #     lines = settings_file.readlines()

                #     for i, l in enumerate(lines):
                #         if 'APP_DIRS' in l:
                #             lines[i-1] = lines[i-1].replace('\n', '')
                #             exploded = lines[i-1].split(',')
                #             exploded[1] += f' + [os.path.join(BASE_DIR, \'./{self.components_base}\') + comp for comp in COMPONENTS_DIRS],\n'
                #             lines[i-1] = ''.join(exploded)
                #             break
                        
                #     settings_file.close()

                # with open(settings_path, 'w') as settings_file:
                #     lines = "".join(lines)
                #     settings_file.write(lines)
                #     settings_file.close()

                # # ADD BUILTIN COMPONENT_TAGS
                # lines = []
                # with open(componentsfile_path, 'w'), open(settings_path, 'r+') as settings_file: 
                #     lines = settings_file.readlines()

                #     for i, l in enumerate(lines):
                #         if 'OPTIONS' in l[i:]:
                #             lines[i-1] = lines[i-1].replace('\n', '')
                #             exploded = lines[i-1].split(',')
                #             exploded[1] += f' + [os.path.join(BASE_DIR, \'./{self.components_base}\') + comp for comp in COMPONENTS_DIRS],\n'
                #             lines[i-1] = ''.join(exploded)
                #             break
                #     settings_file.close()

                # with open(settings_path, 'w') as settings_file:
                #     lines = "".join(lines)
                #     settings_file.write(lines)
                #     settings_file.close()
                
            # else:
            #     self.stdout.write('>> Components file already initialized.')
        else: 
            self.stdout.write('>> Error: Initialization path cannot be empty.')
        if generate:

            generated = True

            if components:
                
                for i, comp in enumerate(components):
                    comp_path_array = str(comp).split('/')
                    comp_name = str(comp_path_array[-1])
                    class_comp_name = ''.join(
                        s.capitalize() for s in comp_name.split('_')
                    ) if '_' in comp_name else comp_name.capitalize() 

                    extensions = ['css', 'html', 'js', 'py']

                    path =  f'{self.root}/{"/".join(comp_path_array)}/'
                    module_path = comp_path_array[0]
                    components_path = self.root_app / 'components.py'

                    Path(path).mkdir(parents=True, exist_ok=True)

                    templ_replacement = {
                        'name': comp_name,
                        'class_name': class_comp_name
                    }

                    for ext in extensions:
                        
                        filepath = path + comp_name + '.' + ext
                        templpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', f'../gentemplates/{ext}.templ'))

                        if not os.path.exists(filepath):
                            # CREATE FILES
                            with open(templpath, 'r') as templ_file, open(filepath, 'w') as out_file:
                                source = Template(templ_file.read())
                                filled_templ = source.substitute(templ_replacement)
                                out_file.write(filled_templ)
                        else:
                            generated = False
                            
                    if generated:
                        # ADD COMPONENT TO components.py file
                        with open(components_path, 'a') as components_file:
                            importline = f'from {str(comp).replace("/", ".")} import {comp_name}\n'

                            components_file.write(importline)
                            components_file.close()

                        self.stdout.write(f'>> Component {comp_name} generated in {"/".join(comp_path_array)}/')
                    else:
                        self.stdout.write(f'>> Component {comp_name} already exists.')