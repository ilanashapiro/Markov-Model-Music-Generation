import xml.etree.ElementTree as ET

class Parser:
    def __init__(self, filename):
        self.root = ET.parse(filename).getroot()
        self.categories_dict = {}
        self.chords_dict = {}
        self.normalized_categories_dict = {}
        self.initial_transition_matrix = {}
        self.smallest_note_value = None
        self.parse_categories()

    def parse_categories(self):
        prev_note = None
        prev_duration = None
        in_chord = False
        note = None
        chord = None

        for part in self.root.findall('part'):
            for measure in part.findall('measure'):
                for note_info in measure.findall('note'):

                    duration = note_info.find('duration').text

                    if int(duration) == 1 and not self.smallest_note_value and note_info.find('type') is not None:
                        self.smallest_note_value = self.switch_note_value(note_info.find('type').text)

                    if note_info.find('pitch') is not None:
                        value = note_info.find('pitch').find('step').text if note_info.find('pitch').find('step') is not None else ''
                        octave = note_info.find('pitch').find('octave').text if note_info.find('pitch').find('octave') is not None else ''
                        accidental_info = note_info.find('accidental').text if note_info.find('accidental') is not None else None
                        accidental = '' if accidental_info is None else ('#' if accidental_info == 'sharp' else 'b' )
                        note = value + accidental + octave

                        if note_info.find('chord') is not None:
                            if in_chord:
                                chord.append(note)
                            else:
                                chord = [prev_note, note]
                            in_chord = True
                        elif in_chord and note_info.find('chord') is None:
                            in_chord = False
                            self.insert(self.chords_dict, tuple(chord), prev_duration)
                            self.insert(self.categories_dict, tuple(chord), prev_duration)
                        else:
                            self.insert(self.categories_dict, note, duration)
                    else: # means that: note_info.find('rest') != None
                        note = 'R'

                    prev_note = note
                    prev_duration = duration
        for key in self.categories_dict:
            print(key, self.categories_dict[key])

    def insert(self, dict, type, duration):
        if type in dict:
            if duration in dict[type]:
                dict[type][duration] = dict[type][duration] + 1
            else:
                dict[type][duration] = 1
        else:
            dict[type] = {}
            dict[type][duration] = 1

    def normalize_categories(self):
        for note in self.categories_dict:
            self.normalized_categories_dict[note] = {}
            total_count = 0
            for duration in self.categories_dict[note]:
                total_count += self.categories_dict[note][duration]
            for duration in self.categories_dict[note]:
                self.normalized_categories_dict[note][duration] = self.categories_dict[note][duration] / total_count
        # print(self.normalized_categories_dict)

    def get_initial_transition_matrix(self):
        self.initial_transition_matrix = {}

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
    parser.normalize_categories()
