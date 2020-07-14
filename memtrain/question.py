class Question:
    '''Manages the current cue and response interface'''
    def __init__(self, connection):
        self.conn = connection
        self.cur = conn.cursor()

    def get_value(value, value_id):
        self.cur.execute('''SELECT {} FROM {} WHERE {} = (?)'''
                         .format(value, value + 's', value + '_id'),
                         (str(value_id), ))
        rows = self.cur.fetchall()
        return rows[0][0]

    def get_cue(cue_id):
        return self.get_value('cue', cue_id)

    def get_response(response_id):
        return self.memtrain_get_value('response', response_id)

    def get_mtags(response_id):
        # Translate response_id into mtag_id
        self.cur.execute('''SELECT mtag_id FROM responses_to_mtags
                    WHERE response_id = (?)''', (str(response_id), ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        out = []

        # Translate mtag_id to mtag
        for mtag_id in rows:
            out.append(self.memtrain_get_value('mtag', mtag_id))

        return out

    def get_placement(cue_id, response_id):
        self.cur.execute('''SELECT placement FROM cues_to_responses
                         WHERE cue_id = (?) AND response_id = (?)''',
                         (str(cue_id), str(response_id)))
        rows = self.cur.fetchall()
        return rows[0][0]

    def get_responses_by_mtag(mtag):
        # Translate mtag_id to mtag
        self.cur.execute('''SELECT mtag_id FROM mtags WHERE mtag = (?)''',
                         (mtag, ))
        rows = self.cur.fetchall()
        rows = list(map(lambda x: x[0], rows))

        # Translate mtag_id to response_id
        response_ids = []

        for mtag_id in rows:
            self.cur.execute('''SELECT response_id FROM responses_to_mtags
                             WHERE mtag_id = (?)''', (mtag_id, ))
            rows = self.cur.fetchall()
            response_ids.append(rows[0][0])

        # Translate response_id to response
        out = []

        for response_id in response_ids:
            out.append(memtrain_get_value('response', response_id))

        return out

    def is_plural(string):
        return string[-1] == 's'

    plural_responses = [i for i in responses if self.is_plural(i)]
    nonplural_responses = [i for i in responses if not self.is_plural(i)]

    