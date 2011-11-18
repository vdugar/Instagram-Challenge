"""
Usage: python instagram.py source_image NO_OF_SHREDS
"""

import sys
from PIL import Image, ImageFilter, ImageChops

img = Image.open(sys.argv[1])
COLS = int(sys.argv[2])
shred_method=sys.argv[3]
width, height = img.size
SHRED_WIDTH = width / COLS
seq_final = []
BEFORE, AFTER = 1, 2
LEFT, RIGHT = 1, 2
img_data=img.getdata()

# Creating the mask which will be used to detect edges
mask = Image.new('RGB', (SHRED_WIDTH * 2, height))
white = Image.new('RGB', (2, height), (255, 255, 255))
mask.paste(white, (SHRED_WIDTH - 1, 0))

# Extracting all the shreds to save computation
shreds = []
for i in range(0, COLS):
    shreds.append(img.crop((i * SHRED_WIDTH, 0, (i + 1) * SHRED_WIDTH, height)))

# Edge-detection method

def get_portion(seq):
    """
    Returns the portion corresponding to this sequence number.
    """
    return shreds[seq]

def compare_sequences(seq1, seq2):
    """
    Compares the two images to see if they fit together or not.
    The images are put together in the order in which they are passed.
    Takes as input sequence numbers w.r.t the original jumbled image.
    Sequence numbers as 0-based.
    """
    img1 = get_portion(seq1)
    img2 = get_portion(seq2)
    composed = Image.new('RGB', (SHRED_WIDTH * 2, height))
    composed.paste(img1, (0, 0))
    composed.paste(img2, (SHRED_WIDTH, 0))
    filtered = composed.filter(ImageFilter.FIND_EDGES)
    # masked = ImageChops.multiply(filtered, mask)
    masked = filtered.convert("L")

    # Checking to see if an edge was found at the border
    data = masked.getdata()
    edge1 = [data[SHRED_WIDTH * 2 * y + SHRED_WIDTH - 1] for y in xrange(0, height)]
    edge2 = [data[SHRED_WIDTH * 2 * y + SHRED_WIDTH] for y in xrange(0, height)]
    avg_color1 = sum(edge1) * 1.0 / height
    avg_color2 = sum(edge2) * 1.0 / height
    if avg_color1 > avg_color2: avg_color = avg_color1
    else: avg_color = avg_color2
    if avg_color < 40:
        return True, avg_color
    else:
        return False, -1

def best_match(seq, order):
    """
    Returns the best match for this shred based on the order of appearance.
    Looks only for shreds that are unmatched so far.
    """
    best_color = 255
    best_match = -1
    for i in range(0, COLS):
        if i not in seq_final and i != seq:
            if order == BEFORE:
                matched, color = compare_sequences(seq, i)
            elif order == AFTER:
                matched, color = compare_sequences(i, seq)
            if matched:
                if color < best_color:
                    best_match = i
                    best_color = color
    return best_match

def unshred_edge():
    """
    Unshreds the source image using edge detection, and outputs it as unshredded.jpg
    """

    # First, let's find two sequences that match
    match = best_match(0, BEFORE)
    if match != -1:
        seq_final.extend([0, match])
    else:
        # Probably the first shred is the last shred in the unshredded image.
        # Let's look for a matching shred before this one.
        seq_final.extend([best_match(0, AFTER), 0])

    # Now, let's just grow the unshredded image by adding segments to the ends
    # of the already discovered images
    while len(seq_final) < COLS:
        prev_seq = list(seq_final)
        print seq_final
        # First, look for a match to come before the first image in the matched sequence
        match = best_match(seq_final[0], AFTER)
        if match != -1:
            seq_final.insert(0, match)
        #Now, look for a match at the end
        match = best_match(seq_final[-1], BEFORE)
        if match != -1:
            seq_final.append(match)
        # Check if anything has changed. If not, no new sequences have been found.
        if seq_final == prev_seq:
            break

    # Now, let's just output the unshredded image
    output = Image.new('RGB', (width, height))
    for i, seq in enumerate(seq_final):
        output.paste(get_portion(seq), (SHRED_WIDTH * i, 0))

    output.save('unshredded.jpg')

# Euclidean distance method

def get_average_pixel(x, y, depth, side):
    """
    Returns the average pixel over 'depth' depending on side.
    """
    avg_pixel = [0, 0, 0]
    for i in range(0, depth):
        pixel = img_data[y * width + x]
        avg_pixel = [sum(pair) for pair in zip(avg_pixel, pixel)]
        if side == LEFT: x -= 1
        else: x += 1
    avg_pixel = [x * 1.0 / depth for x in avg_pixel]
    return avg_pixel

def euclidean_dist(p1, p2):
    """
    Returns the Euclidean distance between two pixels.
    """
    return (sum([(p1[i] - p2[i]) ** 2 for i in range(0, 3)])) ** 0.5

def compare_euclidean_distance(seq1, seq2):
    """
    Attempts to detect an edge by comparing the Euclidean distance over pixel averages.
    """
    x1 = (seq1 + 1) * SHRED_WIDTH - 1
    x2 = seq2 * SHRED_WIDTH
    sum_euc_dist=0
    for i in xrange(0, height):
        sum_euc_dist += euclidean_dist(
                        get_average_pixel(x1, i, 8, LEFT),
                        get_average_pixel(x2, i, 8, RIGHT))
    avg_euc_dist = sum_euc_dist * 1.0 / height
    if avg_euc_dist < 75:
        return True, avg_euc_dist
    else:
        return False, avg_euc_dist


def best_match_euclidean(seq, order):
    """
    Looks for the best match, only among the unmatched sequences.
    """
    best_match = -1
    best_euclidean = 255
    for i in range(0, COLS):
        if i not in seq_final and i != seq:
            if order == BEFORE:
                matched, dist = compare_euclidean_distance(seq, i)
            elif order == AFTER:
                matched, dist = compare_euclidean_distance(i, seq)
            if matched:
                if dist < best_euclidean:
                    best_match, best_euclidean = i, dist
    return best_match

def unshred_euclidean():
    """
    Attempts to unshred using the Euclidean distance between pixel averages.
    Output file is unshredded.jpg
    """
    # First, let's find two sequences that match
    match = best_match_euclidean(0, BEFORE)
    if match != -1:
        seq_final.extend([0, match])
    else:
        # Probably the first shred is the last shred in the unshredded image.
        # Let's look for a matching shred before this one.
        seq_final.extend([best_match_euclidean(0, AFTER), 0])

    # Now, let's just grow the unshredded image by adding segments to the ends
    # of the already discovered images
    while len(seq_final) < COLS:
        prev_seq = list(seq_final)
        print seq_final
        # First, look for a match to come before the first image in the matched sequence
        match = best_match_euclidean(seq_final[0], AFTER)
        if match != -1:
            seq_final.insert(0, match)
        #Now, look for a match at the end
        match = best_match_euclidean(seq_final[-1], BEFORE)
        if match != -1:
            seq_final.append(match)
        # Check if anything has changed. If not, no new sequences have been found.
        if seq_final == prev_seq:
            break

    # Now, let's just output the unshredded image
    output = Image.new('RGB', (width, height))
    for i, seq in enumerate(seq_final):
        output.paste(get_portion(seq), (SHRED_WIDTH * i, 0))

    output.save('unshredded.jpg')

if __name__ == '__main__':
    if shred_method == 'edge':
        unshred_edge()
    elif shred_method == 'euc':
        unshred_euclidean()
    else:
        exit(-1)