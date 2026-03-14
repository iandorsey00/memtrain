from memtrain import __version__


class SettingError(Exception):
    pass


class Settings:
    '''Manage settings for memtrain'''

    BOOLEAN_LABELS = ['level1', 'level2', 'level3']
    INTEGER_LABELS = ['nquestions']
    STRING_LABELS = ['title']

    def __init__(self):
        self.version = __version__
        self.settings = {
            'level1': True,
            'level2': True,
            'level3': True,
            'nquestions': 0,
            'title': '',
        }
        self.all_labels = ['title', 'level1', 'level2', 'level3', 'nquestions']
        self.level = ''
        self.session_mode = 'adaptive'

    def load_settings(self, settings_row):
        '''Load settings from CSV row'''
        settings_row = ''.join(settings_row.split())
        settings_row = settings_row[len('settings:'):]
        settings_row = settings_row.split(',')

        for setting in settings_row:
            if not setting:
                continue

            if setting[0] == '!':
                label = setting[1:]
                if label in self.BOOLEAN_LABELS:
                    self.settings[label] = False
                else:
                    raise SettingError(f"'{setting}': Invalid setting.")

            elif '=' in setting:
                try:
                    label, raw_value = setting.split('=', 1)
                    param = int(raw_value)
                    if label in self.INTEGER_LABELS:
                        self.settings[label] = param
                    else:
                        raise SettingError
                except (ValueError, SettingError):
                    raise SettingError(f"'{setting}': Invalid setting.")

            elif setting in self.BOOLEAN_LABELS:
                self.settings[setting] = True

            else:
                raise SettingError(f"'{setting}': Invalid setting.")

    def set_title(self, title_row):
        '''Set the title'''
        self.settings['title'] = title_row[0]

    def print_settings(self):
        '''Print labels and parameters for each setting.'''
        print("Label".ljust(20) + "Parameter".ljust(20))
        print()
        for label in self.all_labels:
            print(label.ljust(20) + str(self.settings[label]).ljust(20))
