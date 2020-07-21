class Settings:
    '''Manage settings for memtrain'''
    def __init__(self):
        self.version = '0.2a'
        self.settings = dict()
        self.all_labels = ['title', 'level1', 'level2', 'level3', 'nquestions']

        ## Boolean settings
        self.boolean_labels = ['level1', 'level2', 'level3']

        ### Levels

        # Level 1 - Multiple choice questions
        self.settings['level1'] = True
        # Level 2 - Use a hint to respond
        self.settings['level2'] = True
        # Level 3 - Respond on your own
        self.settings['level3'] = True

        ## Integer settings
        self.integer_labels = ['nquestions']

        # nquestions - Number of questions
        self.settings['nquestions'] = 0

        ## String settings
        self.string_labels = ['title']

        # Title
        self.settings['title'] = ''

    def load_settings(self, settings_row):
        '''Load settings from CSV row'''
        # Remove all whitespace characters
        settings_row = ''.join(settings_row.split())
        settings_row = settings_row[len('settings:'):]
        settings_row = settings_row.split(',')

        for setting in settings_row:
            # Negated boolean setting
            if setting[0] == '!':
                label = setting[1:]
                if label in self.boolean_labels:
                    self.settings[label] = False
                else:
                    raise SettingError("'" + setting + "': Invalid setting.")

            # Integer setting
            elif '=' in setting:
                setting = setting.split('=')
                label = setting[0]
                param = int(setting[1])
                try:
                    param = int(param)
                    if label in self.integer_labels:
                        self.settings[label] = param
                except (ValueError, SettingError):
                    raise SettingError("'" + setting + "': Invalid setting.")

            # True boolean setting
            elif setting in self.boolean_labels:
                label = setting
                self.settings[label] = True

            # Else, the setting is invalid.
            else:
                raise SettingError("'" + setting + "': Invalid setting.")

    def set_title(self, title_row):
        '''Set the title'''
        self.settings['title'] = title_row[0]

    def print_settings(self):
        '''Print labels and parameters for each setting.'''
        print("Label".ljust(20) + "Parameter".ljust(20))
        print()
        for label in self.all_labels:
            print(label.ljust(20) + str(self.settings[label]).ljust(20))
