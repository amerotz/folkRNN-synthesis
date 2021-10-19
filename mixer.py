import os
import random
import numpy as np
import argparse
from pedalboard import (
    Pedalboard,
    Compressor,
    Convolution,
    Gain,
    Limiter,
    HighpassFilter
)
import soundfile as sf


def main(input_dir, a, s, output_dir):
    SAMPLE_RATE = 16000

    do_ambience = bool(a)
    do_stomps= bool(s)

    impulse_dir = './impulses'
    ambience_dir = './ambiences'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)



    ###### get stems ######

    print('Loading files...')

    instruments = os.listdir(input_dir)

    songs = {}
    stomps = {}

    # get list of all stems in each instrument
    for i in instruments:
        folder = f'{input_dir}/{i}'

        if i == 'stomps':
            for x in os.listdir(folder):
                key = x.split('_')[0]
                stomps[key] =  f'{folder}/{x}'
        else:
            for x in os.listdir(folder):
                key = x.split('_')[0]

                if not key in songs:
                    songs[key] = []

                songs[key].append(f'{folder}/{x}')

    ambiences = os.listdir(ambience_dir)

    print('Done')


    ###### processing ######

    def pan_audio(audio, angle):
        cos = np.cos(angle)
        sin = np.sin(angle)
        left = pan_audio.const * (cos - sin) * audio
        right = pan_audio.const * (cos + sin) * audio
        return np.dstack((left, right))[0]

    pan_audio.const = np.sqrt(2)/2.0

    def normalize(audio):
        return audio/np.max(np.abs(audio))

    def fade_out(audio, secs):
        length = int(secs*SAMPLE_RATE)
        end = audio.shape[0]
        start = end - length

        # compute fade out curve
        # linear fade
        fade_curve = np.linspace(1.0, 0.0, length)

        # make it stereo
        stereo_fade = np.dstack((fade_curve, fade_curve))[0]

        # apply the curve
        audio[start:end] = audio[start:end] * stereo_fade

    # effects board
    limiter = Pedalboard([
        Limiter()
    ], sample_rate=SAMPLE_RATE)

    track_effects = Pedalboard([
        Gain(gain_db=-10),
        Compressor(threshold_db=-20, ratio=2),
        HighpassFilter(cutoff_frequency_hz=100)
    ], sample_rate=SAMPLE_RATE)


    # reverbs

    irs = os.listdir(impulse_dir)

    reverbs = {i: Pedalboard([Convolution(f'{impulse_dir}/{i}', 0.5)], sample_rate=SAMPLE_RATE) for i in irs}


    ###### songs ######
    print('Processing...')

    # go through each song
    for tune in songs:

        print(tune)

        tempo = float(os.path.basename(songs[tune][0]).split('_')[3])
        bar_len = (60/tempo)*3

        piece_end = int(bar_len*(32*3+1)*SAMPLE_RATE)

        # load all tracks
        # cutting at the calculated end
        audio = {part.split('_')[2]: np.array(sf.read(part)[0][:piece_end]) for part in songs[tune]}

        # generate panning
        pans = np.radians((np.linspace(-1.0, 1.0, len(audio)))*60)
        audio = {a: pan_audio(audio[a], pans[i]) for (i, a) in enumerate(audio)}

        # ambience
        if do_ambience:
            amb_file = sf.read(f'{ambience_dir}/{random.choice(ambiences)}')[0]
            amb_start = int(random.uniform(0, len(amb_file)-piece_end-1))
            amb_file = amb_file[amb_start : amb_start + piece_end]
            audio['ambience'] = amb_file

        if do_stomps:
            audio['stomps'] = pan_audio(sf.read(stomps[tune])[0][:piece_end], 0)

        # apply random reverb
        reverb_type = random.choice(irs)
        print(f'Using {reverb_type} as reverb')
        for a in audio:
            audio[a] = reverbs[reverb_type](audio[a])

        # normalize
        audio = {a: normalize(audio[a]) for a in audio}

        # apply effects
        audio = {a: track_effects(audio[a]) for a in audio}

        audio['stomps'] *= 0.5

        audio = [audio[a] for a in audio]

        # mix
        try:
            new_audio = audio[0][:min(len(audio[0]),piece_end)]
            for i in range(len(audio)):
                new_audio += audio[i][:min(len(audio[i]),piece_end)]

            new_audio /= len(audio)
        except:
            ...

        # apply limiter
        new_audio = limiter(new_audio)

        # fade out the end
        fade_out(new_audio, bar_len)

        # save file
        with sf.SoundFile(f'{output_dir}/{tune}.wav', 'w', samplerate=SAMPLE_RATE, channels=len(new_audio.shape)) as f:
            f.write(new_audio)

    print('Done')

if __name__ == '__main__':
    ###### args ######
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-a', action='store_true')
    parser.add_argument('-s', action='store_true')
    parser.add_argument('output')
    args = parser.parse_args()
    main(args.input, args.a, args.s, args.output)
