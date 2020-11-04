import parse_musicxml
import random
import numpy as np

# I did not write this function. Credit: Akavall on StackOverflow
# https://stackoverflow.com/questions/17118350/how-to-find-nearest-value-that-is-greater-in-numpy-array
def find_nearest_above(my_array, target):
    diff = my_array - target
    mask = np.ma.less_equal(diff, 0)
    # We need to mask the negative differences and zero
    # since we are looking for values above
    if np.all(mask):
        return None # returns None if target is greater than any value
    masked_diff = np.ma.masked_array(diff, mask)
    return masked_diff.argmin()

def generate(seq_len):
    seed = random.uniform(0, 1)
    initial_state_index = find_nearest_above(parser.normalized_initial_transition_matrix, seed)

if __name__ == "__main__":
    parser = parse_musicxml.Parser('Cantabile-Piano.musicxml')
    generate()
