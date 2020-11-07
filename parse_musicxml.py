import xml.etree.ElementTree as ET
import collections
import numpy as np

class Parser:
    def __init__(self, filename):
        self.filename = filename
        self.root = ET.parse(filename).getroot()
        self.output_distribution_dict = collections.OrderedDict()
        self.normalized_output_distribution_matrix = None

        self.initial_transition_dict = collections.OrderedDict()
        self.normalized_initial_transition_matrix = None

        self.transition_probability_dict = collections.OrderedDict()
        self.normalized_transition_probability_matrix = None

        self.sound_objects = []

        self.smallest_note_value = None
        self.tempo = None

        self.order_of_sharps = ['F', 'C', 'G', 'D', 'A', 'E', 'B']
        self.key_sig_dict = {'C':'', 'D':'', 'E':'', 'F':'', 'G':'', 'A':'', 'B':''}
        self.parse()

    def parse(self):
        prev_note = None # the prev note (it may be part of a chord). but this variable itself NEVER stores a chord
        sound_object_to_insert = None # either note or chord
        prev_sound_object = None # either note or chord
        in_chord = False
        note = None
        chord = None
        prev_duration = None
        first_sound_object = None

        self.tempo = self.root.find('part').find('measure').find('direction')
        if self.tempo is not None:
            self.tempo = int(self.tempo.find('sound').attrib['tempo'])
        self.instrument = self.root.find('part-list').find('score-part').find('part-name').text
        if self.instrument == 'Piano':
            self.instrument = 'Acoustic Grand Piano'
        self.name = self.root.find('credit').find('credit-words').text

        for i, part in enumerate(self.root.findall('part')):
            for j, measure in enumerate(part.findall('measure')):
                measure_accidentals = {}
                self.set_key_sig_from_measure(measure)

                for k, note_info in enumerate(measure.findall('note')):
                    duration = note_info.find('type').text
                    duration_value = note_info.find('duration').text # unsure if this is chunk is ever needed later.....
                    if int(duration_value) == 1 and not self.smallest_note_value and note_info.find('type') is not None:
                        self.smallest_note_value = self.rhythm_to_float(note_info.find('type').text)

                    note = None
                    if note_info.find('pitch') is not None:
                        value = note_info.find('pitch').find('step').text if note_info.find('pitch').find('step') is not None else ''
                        octave = note_info.find('pitch').find('octave').text if note_info.find('pitch').find('octave') is not None else ''

                        accidental_info = note_info.find('accidental').text if note_info.find('accidental') is not None else None
                        accidental = '' if accidental_info is None else ('#' if accidental_info == 'sharp' else 'b' )
                        note_for_accidental = value+octave
                        if accidental_info == 'sharp':
                            accidental = '#'
                            measure_accidentals[note_for_accidental] = '#'
                        elif accidental_info == 'flat':
                            accidental = 'b'
                            measure_accidentals[note_for_accidental] = 'b'
                        elif accidental_info == 'natural':
                            accidental = ''
                            measure_accidentals[note_for_accidental] = 'n'
                        elif accidental_info is None and note_for_accidental in measure_accidentals:
                            accidental = '' if measure_accidentals[note_for_accidental] == 'n' else measure_accidentals[note_for_accidental]
                        else:
                            accidental = self.key_sig_dict[value]

                        note = value + accidental + octave
                    elif note_info.find('chord') is None: # means that note_info.find('rest') is not None ----> so we are in a rest
                        note = 'R'

                    if note is not None:
                        is_last_iteration = i == len(self.root.findall('part')) - 1 and j == len(part.findall('measure')) - 1 and k == len(measure.findall('note')) - 1

                        if note_info.find('chord') is not None:
                            # currently, the duration is just  going  to be that of the last note in the chord (can go back to change this later...)
                            if in_chord:
                                chord.append(note)
                            else:
                                chord = [prev_note, note]
                                in_chord = True
                        else:
                            prev_sound_object = sound_object_to_insert
                            if in_chord and note_info.find('chord') is None:
                                in_chord = False
                                sound_object_to_insert = (tuple(sorted(chord)), prev_duration)
                            else:
                                sound_object_to_insert = (prev_note, prev_duration)

                            self.handle_insertion(prev_sound_object, sound_object_to_insert)
                            if first_sound_object is None and prev_sound_object is not None and prev_sound_object[0] is not None:
                                first_sound_object = prev_sound_object
                            if is_last_iteration: #note we're NOT in a chord (i.e. last sound object is NOT a chord)
                                self.handle_insertion(sound_object_to_insert, (note, duration))

                    prev_note = note
                    prev_duration = duration

        if in_chord: # means the last sound object was a chord -- handle this case
            final_chord = (tuple(sorted(chord)), prev_duration)
            self.handle_insertion(sound_object_to_insert, (final_chord, prev_duration))
        else:
            # final sound object was NOT a chord, it was a note
            # set the last note/chord to transition to a quarter rest, rather than nothing
            # then add a transition from the rest back to the first sound object
            # this ensure that everything has a transition defined for it
            self.handle_insertion((note, duration), ('R', "quarter"))
            self.handle_insertion(('R', "quarter"), first_sound_object)

        self.build_matrices()
        # self.print_dict(self.initial_transition_dict)
        # print()
        # self.print_dict(self.transition_probability_dict)
        # print()
        # print(self.sound_objects)

    def set_key_sig_from_measure(self, measure_object):
        key_sig_value = measure_object.find('attributes')
        if key_sig_value is not None:
            key_sig_value = key_sig_value.find('key')
            if key_sig_value is not None:
                key_sig_value = int(key_sig_value.find('fifths').text)

                for note in self.key_sig_dict:
                    self.key_sig_dict[note] = ''
                if key_sig_value == 0:
                    return
                elif key_sig_value < 0:
                    for i in range(len(self.order_of_sharps) - 1, len(self.order_of_sharps)-key_sig_value, -1):
                        self.key_sig_dict[self.order_of_sharps[i]] = 'b'
                else:
                    for i in range(key_sig_value, len(self.order_of_sharps)):
                        self.key_sig_dict[self.order_of_sharps[i]] = '#'


    def build_matrices(self):
        self.build_normalized_transition_probability_matrix()
        self.build_normalized_initial_transition_matrix()

    def build_normalized_initial_transition_matrix(self):
        self.normalized_initial_transition_matrix = np.array(list(init_prob for init_prob in self.initial_transition_dict.values()))
        # convert to probabilities
        self.normalized_initial_transition_matrix = self.normalized_initial_transition_matrix/self.normalized_initial_transition_matrix.sum(keepdims=True)
        # multinomial dist
        self.normalized_initial_transition_matrix = np.cumsum(self.normalized_initial_transition_matrix)

    def build_normalized_transition_probability_matrix(self):
        # initialize matrix to known size
        list_dimension = len(self.sound_objects)
        self.normalized_transition_probability_matrix = np.zeros((list_dimension,list_dimension), dtype=float)

        for i, sound_object in enumerate(self.sound_objects):
            for j, transition_sound_object in enumerate(self.sound_objects):
                if transition_sound_object in self.transition_probability_dict[sound_object]:
                    self.normalized_transition_probability_matrix[i][j] = self.transition_probability_dict[sound_object][transition_sound_object]
        self.normalized_transition_probability_matrix = self.normalized_transition_probability_matrix/self.normalized_transition_probability_matrix.sum(axis=1,keepdims=True)
        self.normalized_transition_probability_matrix = np.cumsum(self.normalized_transition_probability_matrix,axis=1)

    def handle_insertion(self, prev_sound_object, sound_object_to_insert):
        if sound_object_to_insert is not None and sound_object_to_insert[0] is not None:
            if prev_sound_object is not None and prev_sound_object[0] is not None:
                self.insert(self.transition_probability_dict, prev_sound_object, sound_object_to_insert)
            if sound_object_to_insert not in self.sound_objects:
                self.sound_objects.append(sound_object_to_insert)

            if sound_object_to_insert in self.initial_transition_dict:
                self.initial_transition_dict[sound_object_to_insert] = self.initial_transition_dict[sound_object_to_insert] + 1
            else:
                self.initial_transition_dict[sound_object_to_insert] = 1

    def insert(self, dict, value1, value2):
        if value1 in dict:
            if value2 in dict[value1]:
                dict[value1][value2] = dict[value1][value2] + 1
            else:
                dict[value1][value2] = 1
        else:
            dict[value1] = {}
            dict[value1][value2] = 1

    def print_dict(self, dict):
        for key in dict:
            print(key, ":", dict[key])

    def rhythm_to_float(self, duration):
        switcher = {
            "whole": 4,
            "half": 2,
            "quarter": 1,
            "eighth": 1/2,
            "16th": 1/4,
            "32nd": 1/8,
            "64th": 1/16,
            "128th": 1/32
        }
        return switcher.get(duration, None)
