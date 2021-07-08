import sys, os

from django.conf import settings

ROOT = settings.BASE_DIR
APPNAME = str(ROOT).split('/')[-1]
ROOT_APP = ROOT / APPNAME

COMPONENTSFILE_PATH = ROOT_APP / 'components.py'

class AppSettings:
    def __init__(self):
        self.settings = setattr(settings, "COMPONENTS", {})
        self.settings = getattr(settings, "COMPONENTS", {})

    @property
    def AUTODISCOVER(self):
        return self.settings.setdefault("autodiscover", True)

    # @property
    # def COMPONENTS_DIRS(self):
    #     return self.settings.setdefault(
    #         "COMPONENTS_DIRS", 
    #         [ folder for folder in os.listdir(settings.COMPONENTS_BASE) \
    #             if os.path.isdir(os.path.join(settings.COMPONENTS_BASE, folder)) ]
    #     )

    @property
    def LIBRARIES(self):
        # if not os.path.exists(COMPONENTSFILE_PATH):
        #     with open(COMPONENTSFILE_PATH, 'w'): pass
        # else:
        #     print('>> Components file already initialized.')

        # return self.settings.setdefault("libraries", [f'{APPNAME}.components'])
        return self.settings.setdefault("libraries", [])
        

    @property
    def TEMPLATE_CACHE_SIZE(self):
        return self.settings.setdefault("template_cache_size", 128)


app_settings = AppSettings()
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings

# print(getattr(settings, "COMPONENTS"))
print(app_settings.__getattribute__('LIBRARIES'))