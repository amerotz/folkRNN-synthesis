import argparse
import random
import os
import numpy as np
import soundfile as sf
import music21 as m21

def main(file, tempo, output):
    if not os.path.exists(output):
        os.makedirs(output)

    # get tune and bars
    tune = m21.converter.parse(file)
    bars = tune.parts[0].getElementsByClass(m21.stream.Measure)

    # get tempo and calculate bar duration in quarters
    tempo = int(tempo)
    time_signature = tune.recurse().getElementsByClass(m21.meter.TimeSignature)[0]
    beat_duration = time_signature.beatDuration.quarterLength
    bar_duration = time_signature.beatCount * beat_duration

    # calculate duration of one quarter with the given tempo
    quarter_seconds = 60/tempo

    # calculate the length of the whole piece
    duration = bar_duration*(len(bars)+1)*quarter_seconds

    # generate the empty stomping track
    SAMPLE_RATE = 16000
    stomping = np.zeros(int(SAMPLE_RATE*duration))

    # load stomping samples
    stomp_dir = './stomps'
    stomps = [sf.read(f'{stomp_dir}/{s}')[0] for s in os.listdir(stomp_dir)]

    for bar in bars:
        index = int(bar.offset*quarter_seconds*SAMPLE_RATE)
        sample = random.choice(stomps)*random.uniform(0.8,1)
        end_index = min(len(stomping), index + len(sample))
        stomping[index : end_index] += sample[ : end_index-index]

        index = int((bar.offset+bar.duration.quarterLength/2)*quarter_seconds*SAMPLE_RATE)
        sample = random.choice(stomps)*random.uniform(0.8,1)
        end_index = min(len(stomping), index + len(sample))
        stomping[index : end_index] += sample[ : end_index-index]




    with sf.SoundFile(f'{output}/{os.path.basename(file)}_stomps_0_{tempo}.wav', 'w', samplerate=SAMPLE_RATE, channels=len(stomping.shape)) as f:
        f.write(stomping)

if __name__ == '__main__':
    # args
    parser = argparse.ArgumentParser(description='Generate stomping to accompany a tune')
    parser.add_argument('file', help='the source abc file')
    parser.add_argument('tempo', help='the stomping tempo')
    parser.add_argument('output', help='the stomping output')
    args = parser.parse_args()
    main(args.file, args.tempo, args.output)
