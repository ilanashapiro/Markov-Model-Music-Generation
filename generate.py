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

    note_prob = random.uniform(0, 1)
    rhythm_prob = random.uniform(0, 1)
    note_index = find_nearest_above(parser.normalized_initial_transition_matrix, note_prob)
    rhythm_index = find_nearest_above(parser.normalized_output_distribution_matrix[note_index], rhythm_prob)

    sequence[0] = (parser.hidden_states[note_index], parser.observables[rhythm_index])
    curr_index = 1

    while (curr_index < seq_len):
        note_prob = random.uniform(0, 1)
        rhythm_prob = random.uniform(0, 1)

        note_index = find_nearest_above(parser.normalized_transition_probability_matrix[note_index], note_prob)
        if(note_index == None):
            print("ERROR getting note index in probability transition matrix")
            sys.exit(1)

        rhythm_index = find_nearest_above(parser.normalized_output_distribution_matrix[note_index], rhythm_prob)
        if(note_index == None):
            print("ERROR getting note index in output dist rhythm matrix")
            sys.exit(1)

        sequence[curr_index] = (parser.hidden_states[note_index], parser.observables[rhythm_index])
        curr_index += 1
    print(sequence)

if __name__ == "__main__":
    parser = parse_musicxml.Parser('Cantabile-Flute.musicxml')
    generate(100)
