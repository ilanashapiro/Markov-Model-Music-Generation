import xml.etree.ElementTree as ET
import collections

class Parser:
    def __init__(self, filename):
        self.root = ET.parse(filename).getroot()
        self.output_distribution_dict = collections.OrderedDict()
        self.normalized_output_distribution_dict = collections.OrderedDict()

        self.initial_transition_dict = collections.OrderedDict()
        self.normalized_initial_transition_dict = collections.OrderedDict()
        self.initial_transition_matrix = None
        self.normalized_initial_transition_matrix = None

        self.transition_probability_dict = collections.OrderedDict()
        self.normalized_transition_probability_dict = collections.OrderedDict()
        self.normalized_transition_probability_matrix = None

        self.smallest_note_value = None

        self.parse_categories()

    def parse_categories(self):
        prev_note = None # the prev note (it may be part of a chord). but this variable itself NEVER stores a chord
        sound_object_to_insert = None # either note or chord
        prev_sound_object = None # either note or chord
        in_chord = False
        note = None
        chord = None


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
                        is_first_iteration = i == 0 and j == 0 and k == 0
                        is_second_iteration = i == 0 and j == 0 and k == 1
                        is_last_iteration = i == len(self.root.findall('part')) - 1 and j == len(part.findall('measure')) - 1 and k == len(measure.findall('note')) - 1

                        if note_info.find('chord') is not None:
                            if in_chord:
                                chord.append(note)
                            else:
                                chord = [prev_note, note]
                            in_chord = True
                        else:
                            prev_sound_object = sound_object_to_insert
                            if in_chord and note_info.find('chord') is None:
                                in_chord = False
                                sound_object_to_insert = tuple(chord)
                            elif is_last_iteration:
                                sound_object_to_insert = note
                            else:
                                sound_object_to_insert = prev_note

                            if sound_object_to_insert is not None: # it will be None on the first iteration, since we insert based on looking back
                                if prev_sound_object is not None:
                                    self.insert(self.transition_probability_dict, prev_sound_object, sound_object_to_insert)
                                self.insert(self.output_distribution_dict, sound_object_to_insert, duration)

                                if sound_object_to_insert in self.initial_transition_dict:
                                    self.initial_transition_dict[sound_object_to_insert] = self.initial_transition_dict[sound_object_to_insert] + 1
                                else:
                                    self.initial_transition_dict[sound_object_to_insert] = 1

                    prev_note = note

        if in_chord: # means the last sound object was a chord -- handle this case
            self.insert(self.transition_probability_dict, prev_sound_object, sound_object_to_insert)
            self.insert(self.output_distribution_dict, sound_object_to_insert, duration)
            if sound_object_to_insert in self.initial_transition_dict:
                self.initial_transition_dict[sound_object_to_insert] = self.initial_transition_dict[sound_object_to_insert] + 1
            else:
                self.initial_transition_dict[sound_object_to_insert] = 1

        self.insert(self.transition_probability_dict, sound_object_to_insert, 'R') # set the last note/chord to transition to a rest, rather than nothing (this ensure that everything has a transition defined for it)

        self.normalize_initial_transition_dict()
        self.normalize_nested_dict(self.transition_probability_dict, self.normalized_transition_probability_dict)
        self.normalize_nested_dict(self.output_distribution_dict, self.normalized_output_distribution_dict)
        self.build_normalized_transition_probability_matrix()

        self.initial_transition_matrix = list(self.initial_transition_dict.values())
        total_sum_initial_transition_matrix = sum(self.initial_transition_matrix)
        self.normalized_initial_transition_matrix = list(map(lambda elem: elem / total_sum_initial_transition_matrix, self.initial_transition_matrix))

    def insert(self, dict, value1, value2):
        if value1 in dict:
            if value2 in dict[value1]:
                dict[value1][value2] = dict[value1][value2] + 1
            else:
                dict[value1][value2] = 1
        else:
            dict[value1] = {}
            dict[value1][value2] = 1

    def build_normalized_transition_probability_matrix(self):
        # initialize matrix to known size
        list_dimension = len(self.initial_transition_dict)
        self.normalized_transition_probability_matrix = [[None for j in range(list_dimension)] for i in range(list_dimension)]

        for i, (sound_object, v1) in enumerate(self.initial_transition_dict.items()):
            for j, (transition_sound_object, v2) in enumerate(self.initial_transition_dict.items()):
                if transition_sound_object in self.normalized_transition_probability_dict[sound_object]:
                    self.normalized_transition_probability_matrix[i][j] = self.normalized_transition_probability_dict[sound_object][transition_sound_object]
                else:
                    self.normalized_transition_probability_matrix[i][j] = 0

    def normalize_nested_dict(self, input_dict, output_dict):
        for type1 in input_dict:
            output_dict[type1] = {}
            total_count = 0
            for type2 in input_dict[type1]:
                total_count += input_dict[type1][type2]
            for type2 in input_dict[type1]:
                output_dict[type1][type2] = input_dict[type1][type2] / total_count

    def normalize_initial_transition_dict(self):
        total_count = 0
        for sound_object in self.initial_transition_dict:
            total_count += 1
        for sound_object in self.initial_transition_dict:
            self.normalized_initial_transition_dict[sound_object] = self.initial_transition_dict[sound_object] / total_count

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

if __name__ == "__main__":
    parser = Parser('Cantabile-Piano.musicxml')
