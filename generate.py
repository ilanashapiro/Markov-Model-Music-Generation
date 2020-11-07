import parse_musicxml
import random
import numpy as np
import midi_numbers
from midiutil import MIDIFile
import sys
import re

# I did not write this function. Credit: Akavall on StackOverflow
# https://stackoverflow.com/questions/17118350/how-to-find-nearest-value-that-is-greater-in-numpy-array
def find_nearest_above(my_array, target):
    diff = my_array - target
    mask = np.ma.less(diff, 0)
    # We need to mask the negative differences and zero
    # since we are looking for values above
    if np.all(mask):
        return None # returns None if target is greater than any value
    masked_diff = np.ma.masked_array(diff, mask)
    return masked_diff.argmin()

def generate(seq_len, parser):
    sequence = [None] * seq_len

    # comment in for random start note
    # note_prob = random.uniform(0, 1)
    # rhythm_prob = random.uniform(0, 1)
    # note_index = find_nearest_above(parser.normalized_initial_transition_matrix, note_prob)
    # check_null_index(note_index, "ERROR getting note index in initial transition matrix")

    # comment in for seed
    sequence[0] = parser.sound_objects[0]
    note_index = 0
    curr_index = 1

    while (curr_index < seq_len):
        note_prob = random.uniform(0, 1)
        rhythm_prob = random.uniform(0, 1)

        note_index = find_nearest_above(parser.normalized_transition_probability_matrix[note_index], note_prob)
        check_null_index(note_index, "ERROR getting note index in probability transition matrix")

        sequence[curr_index] = parser.sound_objects[note_index]
        curr_index += 1

    return sequence

def check_null_index(index, error_message):
    if(index == None):
        print(error_message)
        sys.exit(1)

def get_note_offset_midi_val(note):
    switcher = {
        "C": 0,
        "C#": 1,
        "Db": 1,
        "D": 2,
        "D#": 3,
        "Eb": 3,
        "E": 4,
        "Fb": 4,
        "E#": 5,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "A": 9,
        "A#": 10,
        "Bb": 10,
        "B": 11,
        "Cb": 11
    }
    return switcher.get(note, 0)

def get_pitch(note):
    octave_info = re.findall('\d+', note)
    if len(octave_info) > 0:
        octave = int(octave_info[0])
        note = ''.join([i for i in note if not i.isdigit()])
        base_octave_val = 12*octave + 24
        note_val = base_octave_val + get_note_offset_midi_val(note)
        return note_val
    return None # this is a rest

if __name__ == "__main__":
    parsers = [parse_musicxml.Parser('sakura_solo.musicxml'), parse_musicxml.Parser('Cantabile-Piano.musicxml'), parse_musicxml.Parser('Cantabile-Flute.musicxml')]
    # parsers  = [parse_musicxml.Parser('Cantabile-Piano.musicxml')]
    for parser in parsers:
        sequence = generate(100, parser)
        track    = 0
        channel  = 0
        time     = 0.0    # In beats
        duration = 1.0   # In beats
        tempo    = parser.tempo if parser.tempo is not None else 80  # In BPM
        volume   = 100  # 0-127, as per the MIDI standard

        output_midi = MIDIFile(1)  # One track, defaults to format 1 (tempo track is created automatically)
        output_midi.addTempo(track, time, tempo)
        output_midi.addProgramChange(track, channel, time, midi_numbers.instrument_to_program(parser.instrument))

        time = 0.0
        for sound_obj in sequence:
            duration = float(parser.rhythm_to_float(sound_obj[1]))
            sound_info = sound_obj[0]
            if type(sound_info) is str:
                pitch = get_pitch(sound_info)
                if pitch is not None: # i.e. if this is not a rest
                    output_midi.addNote(track, channel, pitch, time, duration, volume)
            else: #  type(sound_info) is tuple
                for note in sound_info:
                    pitch = get_pitch(note)
                    output_midi.addNote(track, channel, pitch, time, duration, volume)
                    print(note, pitch)
                print()
            time += duration
        with open(parser.filename + ".mid", "wb") as output_file:
            output_midi.writeFile(output_file)
