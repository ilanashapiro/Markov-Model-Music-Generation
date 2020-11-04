import xml.etree.ElementTree as ET
import collections
import numpy as np

class Parser:
    def __init__(self, filename):
        self.root = ET.parse(filename).getroot()
        self.output_distribution_dict = collections.OrderedDict()
        self.normalized_output_distribution_matrix = None

        self.initial_transition_dict = collections.OrderedDict()
        self.normalized_initial_transition_matrix = None

        self.transition_probability_dict = collections.OrderedDict()
        self.normalized_transition_probability_matrix = None

        self.observables = []
        self.hidden_states = []

        self.smallest_note_value = None

        self.parse()

    def parse(self):
        prev_note = None # the prev note (it may be part of a chord). but this variable itself NEVER stores a chord
        sound_object_to_insert = None # either note or chord
        prev_sound_object = None # either note or chord
        in_chord = False
        note = None
        chord = None
        prev_duration = None

        for i, part in enumerate(self.root.findall('part')):
            for j, measure in enumerate(part.findall('measure')):
                for k, note_info in enumerate(measure.findall('note')):
                    duration = note_info.find('type').text

                    duration_value = note_info.find('duration').text # unsure if this is chunk is ever needed later.....
                    if int(duration_value) == 1 and not self.smallest_note_value and note_info.find('type') is not None:
                        self.smallest_note_value = self.switch_note_value(note_info.find('type').text)

                    note = None
                    if note_info.find('pitch') is not None:
                        value = note_info.find('pitch').find('step').text if note_info.find('pitch').find('step') is not None else ''
                        octave = note_info.find('pitch').find('octave').text if note_info.find('pitch').find('octave') is not None else ''
                        accidental_info = note_info.find('accidental').text if note_info.find('accidental') is not None else None
                        accidental = '' if accidental_info is None else ('#' if accidental_info == 'sharp' else 'b' )
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
                                sound_object_to_insert = tuple(sorted(chord))
                            elif is_last_iteration:
                                sound_object_to_insert = note
                            else:
                                sound_object_to_insert = prev_note

                            if sound_object_to_insert is not None: # it will be None on the first iteration, since we insert based on looking back
                                self.handle_insertion(prev_sound_object, sound_object_to_insert, prev_duration)

                    prev_note = note
                    prev_duration = duration

        if in_chord: # means the last sound object was a chord -- handle this case
            self.handle_insertion(prev_sound_object, sound_object_to_insert, prev_duration)

        self.insert(self.transition_probability_dict, sound_object_to_insert, 'R') # set the last note/chord to transition to a rest, rather than nothing (this ensure that everything has a transition defined for it)

        self.build_matrices()

    # OLD: SHOULD DELETE AS SOON AS I'M SURE I'LL NEVER USE IT ANY MORE
    def normalize_nested_dict(self, input_dict, output_dict):
        for type1 in input_dict:
            output_dict[type1] = {}
            total_count = 0
            for type2 in input_dict[type1]:
                total_count += input_dict[type1][type2]
            for type2 in input_dict[type1]:
                output_dict[type1][type2] = input_dict[type1][type2] / total_count

    def build_matrices(self):
        self.build_normalized_transition_probability_matrix()
        self.build_normalized_initial_transition_matrix()
        self.build_normalized_output_distribution_matrix()

    def build_normalized_initial_transition_matrix(self):
        self.normalized_initial_transition_matrix = np.array(list(init_prob for init_prob in self.initial_transition_dict.values()))
        # convert to probabilities
        self.normalized_initial_transition_matrix = self.normalized_initial_transition_matrix/self.normalized_initial_transition_matrix.sum(keepdims=True)
        # multinomial dist
        self.normalized_initial_transition_matrix = np.cumsum(self.normalized_initial_transition_matrix)

    def build_normalized_transition_probability_matrix(self):
        # initialize matrix to known size
        list_dimension = len(self.hidden_states)
        self.normalized_transition_probability_matrix = np.zeros((list_dimension,list_dimension), dtype=float)

        for i, sound_object in enumerate(self.hidden_states):
            for j, transition_sound_object in enumerate(self.hidden_states):
                if transition_sound_object in self.transition_probability_dict[sound_object]:
                    self.normalized_transition_probability_matrix[i][j] = self.transition_probability_dict[sound_object][transition_sound_object]

        self.normalized_transition_probability_matrix = self.normalized_transition_probability_matrix/self.normalized_transition_probability_matrix.sum(axis=1,keepdims=True)
        self.normalized_transition_probability_matrix = np.cumsum(self.normalized_transition_probability_matrix,axis=1)

    def build_normalized_output_distribution_matrix(self):
        # initialize matrix to known size
        self.normalized_output_distribution_matrix = np.zeros((len(self.hidden_states),len(self.observables)), dtype=float)

        for i, sound_object in enumerate(self.hidden_states):
            for j, transition_sound_object in enumerate(self.observables):
                if transition_sound_object in self.output_distribution_dict[sound_object]:
                    self.normalized_output_distribution_matrix[i][j] = self.output_distribution_dict[sound_object][transition_sound_object]

        self.normalized_output_distribution_matrix = self.normalized_output_distribution_matrix/self.normalized_output_distribution_matrix.sum(axis=1,keepdims=True)
        self.normalized_output_distribution_matrix = np.cumsum(self.normalized_output_distribution_matrix,axis=1)

    def handle_insertion(self, prev_sound_object, sound_object_to_insert, duration_of_sound_object_to_insert):
        if prev_sound_object is not None:
            self.insert(self.transition_probability_dict, prev_sound_object, sound_object_to_insert)
        self.insert(self.output_distribution_dict, sound_object_to_insert, duration_of_sound_object_to_insert)
        if duration_of_sound_object_to_insert not in self.observables:
            self.observables.append(duration_of_sound_object_to_insert)
        if sound_object_to_insert not in self.hidden_states:
            self.hidden_states.append(sound_object_to_insert)

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

    def switch_note_value(self, note_type):
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
        return switcher.get(note_type, None)

    def check_row_stochastic_2d(self, matrix):
        for index, row in enumerate(matrix):
            if sum(row) != 1:
                print("ERROR! The sum in row", index, "is", sum(row))
