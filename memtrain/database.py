import sqlite3

class Database:
    '''Create amd manage the database'''

    def __init__(self):
        '''Create the database'''
        # Initialize SQLite
        self.conn = sqlite3.connect(':memory:')

        # Create tables ###########################################################
        self.conn.execute('''CREATE TABLE cues
                          (cue_id INTEGER PRIMARY KEY,
                          cue TEXT)''')

        self.conn.execute('''CREATE TABLE responses
                          (response_id INTEGER PRIMARY KEY,
                          response TEXT)''')

        self.conn.execute('''CREATE TABLE cues_to_responses
                          (cue_id INTEGER,
                          response_id INTEGER,
                          placement INTEGER,
                          PRIMARY KEY (cue_id, response_id))''')

        self.conn.execute('''CREATE TABLE synonyms
                          (synonym_id INTEGER PRIMARY KEY,
                          synonym TEXT)''')

        self.conn.execute('''CREATE TABLE responses_to_synonyms
                          (response_id INTEGER,
                          synonym_id INTEGER,
                          PRIMARY KEY (response_id, synonym_id))''')

        self.conn.execute('''CREATE TABLE tags
                          (tag_id INTEGER PRIMARY KEY,
                          tag TEXT)''')

        self.conn.execute('''CREATE TABLE responses_to_tags
                          (response_id INTEGER,
                          tag_id INTEGER,
                          PRIMARY KEY (response_id, tag_id))''')

        self.conn.execute('''CREATE TABLE mtags
                          (mtag_id INTEGER PRIMARY KEY,
                          mtag TEXT)''')

        self.conn.execute('''CREATE TABLE responses_to_mtags
                          (response_id INTEGER,
                          mtag_id INTEGER,
                          PRIMARY KEY (response_id, mtag_id))''')

        # Save changes
        self.conn.commit()
        self.cur = self.conn.cursor()

    def populate(self, indices, data_list):
        '''Populate the database with data'''
        # cues table
        cue_list = []

        for data_row in data_list:
            cue = data_row[indices['cue'][0]]
            if cue not in cue_list:
                self.conn.execute('''INSERT INTO cues(cue)
                            VALUES (?)''', (cue, ))
                cue_list.append(cue)

        # responses table
        response_list = []

        for data_row in data_list:
            for index in indices['response']:
                response = data_row[index]
                # Add response only if it's not empty and hasn't been added before.
                if response and response not in response_list:
                    self.conn.execute('''INSERT INTO responses(response)
                                VALUES (?)''', (response, ))
                    response_list.append(response)

        # cues_to_response table
        all_cues = []

        for data_row in data_list:
            # Get the cue_id
            cue = data_row[indices['cue'][0]]
            cue_id = cue_list.index(cue) + 1
            
            # Get the response_id
            for placement, index in enumerate(indices['response']):
                response = data_row[index]

                if response:
                    response_id = response_list.index(response) + 1

                    # To determine placement, see if this cue has come up before.
                    all_cues.append(cue_id)
                    placement = len([i for i in all_cues if i == cue_id])

                    self.conn.execute('''INSERT INTO cues_to_responses(cue_id, response_id, placement)
                                VALUES (?,?,?)''', (cue_id, response_id, placement))

        # synonyms table
        synonym_list = []

        for number, data_row in enumerate(data_list):
            for index in indices['synonym']:
                synonym = data_row[index]
                # Add row only if it's not empty
                if synonym and synonym not in synonym_list:
                    self.conn.execute('''INSERT INTO synonyms(synonym)
                                VALUES (?)''', (synonym, ))
                    synonym_list.append(synonym)

        # responses_to_synonyms table
        responses_to_synonyms_list = []

        for data_row in data_list:
            # Get the response_id
            for placement, index in enumerate(indices['response']):
                response = data_row[index]

                if response:
                    response_id = response_list.index(response) + 1

                    # Get the synonym_id
                    synonym = data_row[indices['synonym'][placement]]

                    if synonym:
                        synonym_id = synonym_list.index(synonym) + 1
                        pair = (response_id, synonym_id)

                        if pair not in responses_to_synonyms_list:
                            self.conn.execute('''INSERT INTO responses_to_synonyms(response_id, synonym_id)
                                        VALUES (?,?)''', pair)
                            responses_to_synonyms_list.append(pair)

        # tags table
        tag_list = []

        for number, data_row in enumerate(data_list):
            for index in indices['tag']:
                tag = data_row[index]
                # Add row only if it's not empty
                if tag and tag not in tag_list:
                    self.conn.execute('''INSERT INTO tags(tag)
                                VALUES (?)''', (tag, ))
                    tag_list.append(tag)

        # responses_to_tags table
        responses_to_tag_list = []

        for data_row in data_list:
            # Get the response_id
            for placement, index in enumerate(indices['response']):
                response = data_row[index]

                if response:
                    response_id = response_list.index(response) + 1

                    # Get the tag_id
                    # Only one tag placement per cue
                    for tag_index in indices['tag']:
                        tag = data_row[tag_index]

                        if tag:
                            tag_id = tag_list.index(tag) + 1
                            pair = (response_id, tag_id)

                            if pair not in responses_to_tag_list:
                                self.conn.execute('''INSERT INTO responses_to_tags(response_id, tag_id)
                                            VALUES (?,?)''', pair)
                                responses_to_tag_list.append(pair)

        # mtags table
        mtag_list = []

        for number, data_row in enumerate(data_list):
            for index in indices['mtag']:
                mtag = data_row[index]
                # Add row only if it's not empty
                if mtag and mtag not in mtag_list:
                    self.conn.execute('''INSERT INTO mtags(mtag)
                                VALUES (?)''', (mtag, ))
                    mtag_list.append(mtag)

        # responses_to_mtags table
        responses_to_mtag_list = []

        for data_row in data_list:
            # Get the response_id
            for placement, index in enumerate(indices['response']):
                response = data_row[index]

                if response:
                    response_id = response_list.index(response) + 1

                    # Get the mtag_id
                    # Only one mtag placement per cue
                    for mtag_index in indices['mtag']:
                        mtag = data_row[mtag_index]

                        if mtag:
                            mtag_id = mtag_list.index(mtag) + 1
                            pair = (response_id, mtag_id)

                            if pair not in responses_to_mtag_list:
                                self.conn.execute('''INSERT INTO responses_to_mtags(response_id, mtag_id)
                                            VALUES (?,?)''', pair)
                                responses_to_mtag_list.append(pair)

        # Save changes
        self.conn.commit()

    # Helper methods ##########################################################
    def query(self, columns, tables):
        '''Run a simple SELECT columns FROM tables query'''
        self.cur.execute('''SELECT {} FROM {}'''.format(columns, tables))
        rows = self.cur.fetchall()
        columns = len(columns.split(','))
        if columns == 1:
            rows = list(map(lambda x: x[0], rows))

        return rows

    def get_all_responses(self):
        return self.query('response', 'responses')

    def get_all_response_ids(self):
        return self.query('response_id', 'responses')

    def get_all_response_ids_by_tag(self, tag):
        self.cur.execute('''SELECT tag_id FROM tags
                    WHERE tag = (?)''', (str(tag), ))
        rows = self.cur.fetchall()
        tag_id = rows[0][0]
        self.cur.execute('''SELECT response_id FROM responses_to_tags
                            WHERE tag_id = (?)''', (str(tag_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        return rows

    def get_all_cue_response_id_pairs(self):
        return self.query('cue_id, response_id', 'cues_to_responses')

