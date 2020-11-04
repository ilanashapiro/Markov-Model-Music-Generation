import parse_musicxml
import random
import numpy as np
import sys

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

def generate(seq_len):
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

    print(sequence)

def check_null_index(index, error_message):
    if(index == None):
        print(error_message)
        sys.exit(1)

if __name__ == "__main__":
    parser = parse_musicxml.Parser('Cantabile-Flute.musicxml')
    generate(100)
