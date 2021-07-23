from typing import Callable
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
import os, sys
from string import Template
from importlib import reload
from copy import deepcopy

from ...slimit.minifier import minify
from ...csscompressor import compress

class Command(BaseCommand):
    help = '>> Django Components manager. This tool is used to maintain django_components projects.'

    root = settings.BASE_DIR
    appname = str(settings.BASE_DIR).split('/')[-1]
    root_app = f'{root}/{appname}'
    components_base = ''

    def save(self, filepath, lines, callback: Callable = None):
        with open(filepath, 'w') as file:
            lines = ''.join(lines)
            file.write(lines)
            file.close
        
        if callback:
            callback()

    def cancel(self, filepath, backup):
        self.save(
            filepath=filepath, 
            lines=backup, 
            callback=lambda: (
                os.remove(f'{self.root_app}/components.py'),
                self.stdout.write('>> Operation aborted.')
            )
        )

    def add_arguments(self, parser):
        parser.add_argument('-i', '--initialize', type=str, help='Set up Django Components')
        parser.add_argument('-g', '--generate', action='store_true', help='Generate elements')
        parser.add_argument('-c', '--component', nargs='+', type=str, help='Select component as element to operate with')
        parser.add_argument('-p', '--compile', type=str, help='Compile components statics (JS/CSS)')

    def handle(self, *args, **kwargs):
        initialize = kwargs['initialize']
        generate = kwargs['generate']
        components = kwargs['component']
        compile = kwargs['compile']

        if initialize:

            componentsfile_path = f'{self.root_app}/components.py'
            settings_path = f'{self.root_app}/settings.py'
            self.components_base = initialize
            self.components_parent = self.components_base.split('/')[0]

            current_step = 0
            steps_description = [
                'creating component.py file', 
                'importing os module',
                'adding component constants',
                'adding component directories into templates',
                'adding tags as builtin',
                'adding component directories into static',
            ]
            steps = len(steps_description)

            if not os.path.exists(componentsfile_path):
                # STARTING
                # self.stdout.write('>> Creating component.py file and adding it to your project...')
                self.stdout.write('>> Django components plugin initialization started...')

                lines, backup = [], []

                with open(settings_path, 'r+') as settings_file, \
                    open(componentsfile_path, 'w'):

                    backup = settings_file.readlines()

                    lines = deepcopy(backup)

                    self.stdout.write('\n')

                    # CHECK IF component.py HAS BEEN CREATED
                    if os.path.isfile(componentsfile_path):
                        self.stdout.write(f'>> File components.py created successfully. 4%')
                        current_step += 1
                    else: 
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        exit()
                    
                    self.stdout.write('\n')

                    ## STEP 1
                    for i, l in enumerate(lines):

                        # IMPORTING 'os' MODULE
                        if current_step == 1:
                            if 'import' in l:
                                if 'os' not in sys.modules[f'{self.appname}.settings'].__dir__():
                                    lines.insert(i + 1, 'import os\n')
                                    break
                                else:
                                    self.stdout.write(f'>> (!) Module \'os\' detected.')
                                    break
                        
                    self.save(filepath=settings_path, lines=lines)
                    reload(sys.modules[f'{self.appname}.settings'])
                
                    # CHECK IF IMPORTED
                    if 'os' in sys.modules[f'{self.appname}.settings'].__dir__():
                        self.stdout.write(f'>> Module \'os\' imported correctly. {int((100*current_step)/steps)}%')
                        current_step += 1
                        Path(f'{settings.BASE_DIR}/{self.components_base}').mkdir(parents=True, exist_ok=True)
                    else:
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        self.cancel(filepath=settings_path, backup=backup)
                        exit()
                    
                    self.stdout.write('\n')

                    self.stdout.write('>> Adding required configuration...')

                    ## STEP 2
                    for i, l in enumerate(lines):
                        # WRITING COMPONENT SETTINGS
                        if current_step == 2:
                            if 'COMPONENTS' not in sys.modules[f'{self.appname}.settings'].__dir__():
                                if 'BASE_DIR' in l:
                                    lines.insert(
                                        i + 2,
                                        '\n# DJANGO_COMPONENTS PLUGIN\n'
                                        'COMPONENTS = {\n'
                                            '\t\'libraries\': [\n'
                                                f'\t\t\'{self.appname}.components\'\n'
                                            '\t]\n'
                                        '}\n'
                                        'COMPONENTS_BASE = ' + f'f\'{{BASE_DIR}}/{self.components_base}\''
                                        '\nCOMPONENTS_DIRS = [ dir for dir in os.listdir(COMPONENTS_BASE) if os.path.isdir(os.path.join(COMPONENTS_BASE, dir)) ]\n'
                                    )
                                    self.stdout.write(f'>>    - Added \'COMPONENT\' constant to settings. {int((100*current_step)/steps)}%')
                                    break
                            else:
                                self.stdout.write(f'>> (!) Constant \'COMPONENTS\' detected.')
                                break

                    self.save(filepath=settings_path, lines=lines)
                    reload(sys.modules[f'{self.appname}.settings'])
                
                    # CHECK IF IMPORTED
                    if 'COMPONENTS' in sys.modules[f'{self.appname}.settings'].__dir__():
                        current_step += 1
                    else:
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        self.cancel(filepath=settings_path, backup=backup)
                        exit()

                    ## STEP 3
                    string = f'[os.path.join(BASE_DIR, \'{self.components_base}/\') + comp for comp in COMPONENTS_DIRS if comp != \'__pycache__\']'
                    for i, l in enumerate(lines):
                        # ADDING TO TEMPLATES
                        if current_step == 3:
                            if 'APP_DIRS' in l:
                                lines[i-1] = lines[i-1].replace('\n', '')
                                exploded = lines[i-1].split(',')
                                exploded[1] += f' + {string},\n'
                                lines[i-1] = ''.join(exploded)
                            
                                current_step += 1

                    self.save(filepath=settings_path, lines=lines)
                    # reload(sys.modules[f'{self.appname}.settings'])

                    if current_step == 4:
                        self.stdout.write(f'>>    - Added component directories to templates. {int((100*current_step)/steps)}%')
                    else:
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        self.cancel(filepath=settings_path, backup=backup)
                        exit()

                    ## STEP 4
                    for i, l in enumerate(lines):
                        # ADDING BUILTINS
                        if 'context_processors' in l and 'OPTIONS' in lines[i-1]:
                            lines.insert(i, (
                                '\t\t\t\'builtins\': [\n'
                                    '\t\t\t\t\'django_components.templatetags.component_tags\',\n'
                                '\t\t\t],\n'
                            ))
                            current_step += 1

                    self.save(filepath=settings_path, lines=lines)

                    if current_step == 5:
                        self.stdout.write(f'>>    - Added tags to context_processors. {int((100*current_step)/steps)}%')
                    else:
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        self.cancel(filepath=settings_path, backup=backup)
                        exit()

                    ## STEP 5
                    for i, l in enumerate(lines):
                        # ADDING TO STATIC
                        if 'STATICFILES_DIRS' not in sys.modules[f'{self.appname}.settings'].__dir__():
                            settings_file.write(
                                (
                                    f'STATICFILES_DIRS = {string} + \\\n'
                                    '[] # PLACE YOUR OWN DIRECTORIES HERE' 
                                )
                            )
                        else:
                            if 'STATICFILES_DIRS' in l:
                                lines[i] = lines[i].replace(
                                    'STATICFILES_DIRS =', 
                                    'STATICFILES_DIRS = ' + f'{string} + \\\n'
                                )

                    self.save(filepath=settings_path, lines=lines)

                    if current_step == len(steps_description)-1:
                        current_step += 1
                        self.stdout.write(f'>>    - Added component directories to static. {int((100*current_step)/steps)}%')
                    else:
                        self.stdout.write(f'>> Error on step {current_step} \'{steps_description[current_step]}\'.')
                        self.cancel(filepath=settings_path, backup=backup)
                        exit()
                
                settings_file.close()
                
            else:
                self.stdout.write('>> Components file already initialized.')
        if generate:

            generated = True

            if 'COMPONENTS_BASE' in sys.modules[f'{self.appname}.settings'].__dir__():

                if components:
                    
                    for i, comp in enumerate(components):
                        comp_path_array = str(comp).split('/')
                        comp_name = str(comp_path_array[-1])
                        class_comp_name = ''.join(
                            s.capitalize() for s in comp_name.split('_')
                        ) if '_' in comp_name else comp_name.capitalize() 

                        extensions = ['css', 'html', 'js', 'py']

                        # path =  f'{self.root}/{"/".join(comp_path_array)}/'
                        # module_path = comp_path_array[0]
                        components_path = f'{self.root_app}/components.py'

                        # Path(path).mkdir(parents=True, exist_ok=True)

                        templ_replacement = {
                            'name': comp_name,
                            'class_name': class_comp_name
                        }

                        for ext in extensions:
                            
                            filedir = f'{settings.COMPONENTS_BASE}/{comp_name}/'
                            filepath = filedir + comp_name + '.' + ext

                            templpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', f'../gentemplates/{ext}.templ'))

                            Path(filedir).mkdir(parents=True, exist_ok=True)

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
                                relative_comp_base = str(settings.COMPONENTS_BASE).split(str(settings.BASE_DIR))[1][1:]
                                importline = f'\nfrom {relative_comp_base.replace("/", ".")}.{comp} import {comp_name}\n'

                                components_file.write(importline)
                                components_file.close()

                            self.stdout.write(f'>> Component {comp_name} generated in {relative_comp_base}/{comp}/')
                        else:
                            self.stdout.write(f'>> Component {comp_name} already exists.')
            else:
                self.stdout.write(f'>> Plugin settings not initialized.')
        
        static_path = ''
        if compile:

            extensions = [ 'css', 'js' ]

            if compile != '@default':
                
                static_path = f'{self.root}/{compile}'
            else:
                static_path = f'{self.root}/{settings.STATIC_ROOT}'
            
            if 'COMPONENTS_BASE' in sys.modules[f'{self.appname}.settings'].__dir__():

                if os.path.exists(static_path):
                    self.stdout.write(f'>> Creating static files at {settings.STATIC_ROOT}/ ...')
                    # Path(f'{self.root}/tmp').mkdir(parents=True, exist_ok=True)

                    for ext in extensions:

                        self.stdout.write('\n\n')
                        self.stdout.write(f'>> ------ Reading .{ext} files... ------')

                        if os.path.isfile(f'{self.root}/{settings.STATIC_ROOT}/components.{ext}'):
                            self.stdout.write(f'>> Found existing components.{ext} file at {settings.STATIC_ROOT}/. Overwriting ...')
                            os.remove(f'{self.root}/{settings.STATIC_ROOT}/components.{ext}')
                            self.stdout.write(f'>> Files deleted succesfully.')
                        else:
                            self.stdout.write(f'>> No previous components.{ext} file found at {settings.STATIC_ROOT}/. Creating ...')

                        self.stdout.write(f'>> Reading component directories inside {settings.COMPONENTS_BASE}/')
                        
                        for dir in settings.COMPONENTS_DIRS:
                                with open(f'{settings.COMPONENTS_BASE}/{dir}/{dir}.{ext}', 'r') as in_file:
                                        
                                        with open(f'{static_path}/components.{ext}', 'a') as out_file:

                                            if ext == 'js':
                                                # ARROW FUNCTIONS ARE NOT ALLOWED
                                                content = minify(in_file.read().replace('() =>', 'function()'), mangle=True, mangle_toplevel=True)
                                                out_file.write(content)
                                            elif ext == 'css':
                                                content = compress(in_file.read())
                                                out_file.write(content)
                                
                        self.stdout.write(f'>> Compiling and minification process complete.')
                        
                else:
                    self.stdout.write(f'>> The specified route for static files does not exist. Aborting...')
            else:
                self.stdout.write(f'>> Django Components has not been initialized. Aborting...')