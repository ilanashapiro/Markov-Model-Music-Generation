import xml.etree.ElementTree as ET
import collections

class Parser:
    def __init__(self, filename):
        self.root = ET.parse(filename).getroot()
        self.categories_dict = collections.OrderedDict()
        self.normalized_categories_dict = collections.OrderedDict()
        self.initial_transition_matrix = collections.OrderedDict()
        self.normalized_initial_transition_matrix = collections.OrderedDict()
        self.transition_probability_matrix = collections.OrderedDict()
        self.normalized_transition_probability_matrix = collections.OrderedDict()
        self.smallest_note_value = None
        self.parse_categories()

    def parse_categories(self):
        prev_note = None # the prev note (it may be part of a chord). but this variable itself NEVER stores a chord
        prev_sound_object = None # either note or chord
        prev_duration = None
        in_chord = False
        note = None
        chord = None

        for i, part in enumerate(self.root.findall('part')):
            for j, measure in enumerate(part.findall('measure')):
                for k, note_info in enumerate(measure.findall('note')):
                    duration = note_info.find('duration').text

                    if int(duration) == 1 and not self.smallest_note_value and note_info.find('type') is not None:
                        self.smallest_note_value = self.switch_note_value(note_info.find('type').text)

                    note = None
                    if note_info.find('pitch') is not None:
                        value = note_info.find('pitch').find('step').text if note_info.find('pitch').find('step') is not None else ''
                        octave = note_info.find('pitch').find('octave').text if note_info.find('pitch').find('octave') is not None else ''
                        accidental_info = note_info.find('accidental').text if note_info.find('accidental') is not None else None
                        accidental = '' if accidental_info is None else ('#' if accidental_info == 'sharp' else 'b' )
                        note = value + accidental + octave
                    elif note_info.find('chord') is None: # means that: note_info.find('rest') is not None ----> so we are in a rest
                        note = 'R'

                    if note is not None:
                        is_last_iteration = i == len(self.root.findall('part')) - 1 and j == len(part.findall('measure')) - 1 and k == len(measure.findall('note')) - 1

                        if note_info.find('chord') is not None:
                            if in_chord:
                                chord.append(note)
                            else:
                                chord = [prev_note, note]
                            in_chord = True
                        elif in_chord and note_info.find('chord') is None:
                            in_chord = False
                            curr_sound_object = tuple(chord)
                            if prev_sound_object is not None:
                                self.insert(self.transition_probability_matrix, prev_sound_object, curr_sound_object)
                            prev_sound_object = curr_sound_object
                            self.insert(self.categories_dict, curr_sound_object, prev_duration)
                        elif is_last_iteration:
                            self.insert(self.transition_probability_matrix, prev_sound_object, note)
                            self.insert(self.categories_dict, note, duration)
                        else:
                            if prev_sound_object is not None:
                                self.insert(self.transition_probability_matrix, prev_sound_object, note)
                            prev_sound_object = note
                            self.insert(self.categories_dict, prev_note, duration)

                    if not in_chord:
                        if note in self.initial_transition_matrix:
                            self.initial_transition_matrix[note] = self.initial_transition_matrix[note] + 1
                        else:
                            self.initial_transition_matrix[note] = 1

                    prev_note = note
                    prev_duration = duration

    def insert(self, dict, value1, value2):
        if value1 in dict:
            if value2 in dict[value1]:
                dict[value1][value2] = dict[value1][value2] + 1
            else:
                dict[value1][value2] = 1
        else:
            dict[value1] = {}
            dict[value1][value2] = 1

    def normalize_nested_matrix(self, input_matrix, output_matrix):
        for type1 in input_matrix:
            output_matrix[type1] = {}
            total_count = 0
            for type2 in input_matrix[type1]:
                total_count += input_matrix[type1][type2]
            for type2 in input_matrix[type1]:
                output_matrix[type1][type2] = input_matrix[type1][type2] / total_count
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        self.print_dict(input_matrix)
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        self.print_dict(output_matrix)

    def normalize_initial_transition_matrix(self):
        total_count = 0
        for sound_object in self.initial_transition_matrix:
            total_count += 1
        for sound_object in self.initial_transition_matrix:
            self.normalized_initial_transition_matrix[sound_object] = self.initial_transition_matrix[sound_object] / total_count

        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        self.print_dict(self.initial_transition_matrix)
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        self.print_dict(self.normalized_initial_transition_matrix)

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
    # parser.normalize_matrix(parser.categories_dict)
    parser.normalize_initial_transition_matrix()
