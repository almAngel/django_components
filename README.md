# Python based tool for componentization of Django templates

### Contains:
* Easy initialization: `python manage.py django_components -i`
* Component generation tool: `python manage.py django_components -g -c example`
  - Add `--include-sass` at the end of the command to generate a style.scss file when generating a component.
* Automatic compilation and minification of static files: `python manage.py django_components --compile @default`

> @default is used to specify the destination folder as settings' 'STATIC_ROOT' constant, but specifying another folder is possible within project's root folder.
> Example: python manage.py django_components --compile otherstaticfolder
