import argparse
import os
import random
import music21 as m21
import numpy as np

def main(file, instr, spice, tempo, output):
    spice = float(spice)
    grace_val = 1/8

    # some constants
    PHRASE_LEN = 4
    CUTS_FREQ = np.clip(spice + random.uniform(-0.1, 0.1), 0, 1)
    CUTS_FREQ_MID = CUTS_FREQ/2
    GRACE_FREQ = np.clip(CUTS_FREQ + random.uniform(-0.1, 0.1), 0, 1)
    GRACE_DURATION = m21.duration.Duration(grace_val)
    MAX_BAR_ORNAMENTS = spice*4

    # retrieve music
    tune = m21.converter.parse(file)
    bars = tune.parts[0].getElementsByClass(m21.stream.Measure)

    time_signature = tune.recurse().getElementsByClass(m21.meter.TimeSignature)[0]
    bar_duration = time_signature.beatCount * time_signature.beatDuration.quarterLength
    mid_bar = bar_duration / 2

    key = tune.recurse().getElementsByClass(m21.key.KeySignature)
    if len(key) == 0:
        key = tune.analyze('key')[0]
    else:
        key = key[0]

    # create new score
    new_stream = m21.stream.Score(id='ornaments')
    prev = m21.note.Unpitched()

    # cuts for different instruments

    instruments = {
        'accordion': {
            m21.pitch.Pitch('D4'): m21.pitch.Pitch('E4'),
            m21.pitch.Pitch('D5'): m21.pitch.Pitch('E5'),
            m21.pitch.Pitch('E4'): m21.pitch.Pitch('F#4'),
            m21.pitch.Pitch('E5'): m21.pitch.Pitch('F#5'),
            m21.pitch.Pitch('F#5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('G4'): m21.pitch.Pitch('A4'),
            m21.pitch.Pitch('G5'): m21.pitch.Pitch('B5'),
            m21.pitch.Pitch('A4'): m21.pitch.Pitch('B4'),
            m21.pitch.Pitch('A5'): m21.pitch.Pitch('B5'),
            m21.pitch.Pitch('B3'): m21.pitch.Pitch('D4'),
            m21.pitch.Pitch('B4'): m21.pitch.Pitch('D5'),
            m21.pitch.Pitch('C4'): m21.pitch.Pitch('E4'),
            m21.pitch.Pitch('C5'): m21.pitch.Pitch('E5')
        },
        'fiddle': {
            m21.pitch.Pitch('D4'): m21.pitch.Pitch('E4'),
            m21.pitch.Pitch('D5'): m21.pitch.Pitch('E5'),
            m21.pitch.Pitch('E4'): m21.pitch.Pitch('F#4'),
            m21.pitch.Pitch('E5'): m21.pitch.Pitch('F#5'),
            m21.pitch.Pitch('F4'): m21.pitch.Pitch('G4'),
            m21.pitch.Pitch('F#4'): m21.pitch.Pitch('G4'),
            m21.pitch.Pitch('F#5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('G4'): m21.pitch.Pitch('A4'),
            m21.pitch.Pitch('G5'): m21.pitch.Pitch('B5'),
            m21.pitch.Pitch('A4'): m21.pitch.Pitch('B4'),
            m21.pitch.Pitch('A5'): m21.pitch.Pitch('B5'),
            m21.pitch.Pitch('B3'): m21.pitch.Pitch('C4'),
            m21.pitch.Pitch('B4'): m21.pitch.Pitch('D5'),
            m21.pitch.Pitch('C4'): m21.pitch.Pitch('D4'),
            m21.pitch.Pitch('C5'): m21.pitch.Pitch('D5')
        },
        'flute': {
            m21.pitch.Pitch('E4'): m21.pitch.Pitch('F#4'),
            m21.pitch.Pitch('E5'): m21.pitch.Pitch('F#5'),
            m21.pitch.Pitch('F#4'): m21.pitch.Pitch('A4'),
            m21.pitch.Pitch('F#5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('G4'): m21.pitch.Pitch('A4'),
            m21.pitch.Pitch('G5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('A4'): m21.pitch.Pitch('B4'),
            m21.pitch.Pitch('C5'): m21.pitch.Pitch('D5')
        },
        'whistle': {
            m21.pitch.Pitch('E5'): m21.pitch.Pitch('F#5'),
            m21.pitch.Pitch('E6'): m21.pitch.Pitch('F#6'),
            m21.pitch.Pitch('F#5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('F#6'): m21.pitch.Pitch('A6'),
            m21.pitch.Pitch('G5'): m21.pitch.Pitch('A5'),
            m21.pitch.Pitch('G6'): m21.pitch.Pitch('A6'),
            m21.pitch.Pitch('A5'): m21.pitch.Pitch('B5'),
            m21.pitch.Pitch('C6'): m21.pitch.Pitch('D6')
        }
    }

    velocities = {
        'accordion': 80,
        'fiddle': 60,
        'flute': 80,
        'whistle': 80
    }

    ranges = {
        'accordion': [m21.pitch.Pitch('F3'), m21.pitch.Pitch('G6')],
        'fiddle': [m21.pitch.Pitch('G3'), m21.pitch.Pitch('A7')],
        'flute': [m21.pitch.Pitch('C4'), m21.pitch.Pitch('C7')],
        'whistle': [m21.pitch.Pitch('C5'), m21.pitch.Pitch('B6')]
    }

    accordion_transpose = instr == 'accordion' and random.uniform(0, 1) < 0.75

    def constrain_range(note):
        if accordion_transpose:
            note.octave -= 1
        elif instr == 'whistle':
            note.octave += 1

        while note.pitch < ranges[instr][0]:
            note.octave += 1

        while note.pitch > ranges[instr][1]:
            note.octave -= 1

        return note

    # assigned model
    cuts = instruments[instr]
    offset = 0

    note_vel = velocities[instr]

    # go through each bar
    for i in range(len(bars)-1):

        bar = bars[i]

        # create measure
        m = m21.stream.Measure(number=i)

        # append tempo indication if first one
        if i == 0:
            m.append(m21.tempo.MetronomeMark(number=int(tempo)))

        # keep track of the ornamentation
        bar_ornaments = 0

        # count bars
        if bar.duration.quarterLength < mid_bar:
            offset += 1

        # check if first or last bar of a phrase
        first = (i - offset) % PHRASE_LEN == 0
        last = (i - offset) % PHRASE_LEN == PHRASE_LEN-1

        # go through each elem in the bar
        for current in bar.notes:

            # make all notes fit in range
            current = constrain_range(current)
            pitch_key = m21.pitch.Pitch(current.pitch)

            # if not first or last bar
            # and there is a cut for that note
            # and we are below the ornamentation limit
            if ((not first and not last) and pitch_key in cuts and bar_ornaments < MAX_BAR_ORNAMENTS):

                # try to generate a cut
                # if we are at the start of the bar
                # if we are at the middle of the bar
                # if there are two equal notes
                if ((current.offset == 0 and random.uniform(0,1) < CUTS_FREQ)
                        or (current.offset == mid_bar and random.uniform(0,1) < CUTS_FREQ_MID)
                        or (prev.pitch == current.pitch and random.uniform(0,1) < GRACE_FREQ)):

                    grace = m21.note.Note(cuts[pitch_key], duration=GRACE_DURATION)
                    grace.volume = note_vel
                    m.append(grace)
                    current.duration.quarterLength -= grace_val
                    bar_ornaments += 1

            # append current to new measure
            velocity_val = note_vel + random.randint(-2, 2)
            if current.offset == 0:
                velocity_val += 5
            elif current.offset == mid_bar:
                velocity_val += 3

            current.volume = velocity_val
            m.append(current)
            prev = current

        # append measure to score
        new_stream.append(m)


    # last measure
    last_bar_notes = list(bars[-1].notes)
    last_dur = 0
    i = len(last_bar_notes)-1
    while last_bar_notes[i].pitch.pitchClass != key.tonic.pitchClass and i > 0:
        last_dur += last_bar_notes[i].duration.quarterLength
        i -= 1

    if last_dur == 0:
        last_dur = last_bar_notes[i].duration.quarterLength

    m = m21.stream.Measure(number=len(bars)-1)

    if i != 0:
        # append notes until the tonic
        for note in last_bar_notes[:i]:
            note = constrain_range(note)
            note.volume = note_vel + random.randint(-2, 2)
            m.append(note)

        final = m21.note.Note(last_bar_notes[i].pitch, duration=m21.duration.Duration(quarterLength=last_dur))
        m.append(final)
    else:
        # append only final tonic                                             
        end_note = constrain_range(
            m21.note.Note(f'{key.tonic}{list(bars[-1].notes)[-1].octave}',
                          duration=m21.duration.Duration(quarterLength=6)))
        end_note.volume = note_vel
        m.append(end_note)

    new_stream.append(m)



    # save the file
    filename = ''
    with open(file) as f:
        filename = os.path.basename(f.name)

    #new_stream.show()
    new_stream.write('midi', f'{output}/{filename}_{instr}_{spice}_{tempo}_.mid')

if __name__ == 'main':
   # args
    parser = argparse.ArgumentParser(description='Generate ornamentation and variations for folk tunes')
    parser.add_argument('file', help='the source abc file')
    parser.add_argument('instr', help='the instrument to generate ornamentation for')
    parser.add_argument('spice', help='the "spiciness" of the performance')
    parser.add_argument('tempo', help='the tempo of the performance')
    parser.add_argument('output', help='the destination directory')
    args = parser.parse_args()
    main(args.file, args.instr, args.spice, args.tempo, args.output)
