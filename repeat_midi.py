import music21 as m21
import pretty_midi

def main(file, n, output):
    # use music21 to expand repeats
    tune = m21.converter.parse(file).parts[0].expandRepeats()
    tune.write('midi', output)

    # use pretty midi to repeat
    tune = pretty_midi.PrettyMIDI(file)
    new_tune = pretty_midi.PrettyMIDI()

    for k in tune.key_signature_changes:
        new_tune.key_signature_changes.append(k)
    for t in tune.time_signature_changes:
        new_tune.time_signature_changes.append(t)

    for instr in tune.instruments:
        new_instr = pretty_midi.Instrument(program=instr.program)
        shift = 0
        for i in range(int(n)):
            for note in instr.notes:
                new_note = pretty_midi.Note(
                    velocity=note.velocity, pitch=note.pitch,
                    start=note.start+shift, end=note.end+shift)
                new_instr.notes.append(new_note)
            shift = new_instr.notes[-1].end
        new_tune.instruments.append(new_instr)

    new_tune.write(output)

if __name__ == 'main':
    import argparse
    # args
    parser = argparse.ArgumentParser(description='Repeat a midi file n times')
    parser.add_argument('file', help='Input file')
    parser.add_argument('n', help='times to repeat')
    parser.add_argument('output', help='Output file')
    args = parser.parse_args()

    main(args.file, args.n, args.output)
