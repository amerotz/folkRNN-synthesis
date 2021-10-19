import argparse
import random
import pretty_midi

def main(file, micro, output):
    # open file
    tune = pretty_midi.PrettyMIDI(file)

    shift_perc = float(micro)

    # for each instrument in the file
    for instrument in tune.instruments:
        prev_note_end = 0
        prev_note = instrument.notes[0]

        for note in instrument.notes:

            # randomly change pitch sometimes
            if random.uniform(0, 1) < 0.1*micro:
                if random.uniform(0,1) < 0.5:
                    note.pitch += random.randint(-7, 7)
                else:
                    note.pitch = prev_note.pitch

            # calculate maximum shift delta (a fraction of the duration)
            delta = shift_perc*(note.end - note.start)

            # if the previous note ended
            # after the original start time,
            # use that as new start time,
            # else use the original one with some randomness
            note.start = max(note.start + random.uniform(0, delta), prev_note_end)

            # randomize the note end time
            note.end += random.uniform(-delta, delta)

            # update for next iteration
            prev_note_end = note.end
            prev_note = note

        instrument.notes[-1].end += 10

    tune.remove_invalid_notes()

    # save file
    tune.write(output)

if __name__ == 'main':
    # args
    parser = argparse.ArgumentParser(description='Generate microtimings for midi files')
    parser.add_argument('file', help='the source file')
    parser.add_argument('micro', help='the microtiming percentage')
    parser.add_argument('output', help='the destination file')
    args = parser.parse_args()
    main(args.file, args.micro, args.output)

