import ddsp
import time
import os
from control_models import *
from trn_lib import *
from synthesis_models import *
from load_midi import *
import random
import argparse

###### args ######
parser = argparse.ArgumentParser(description='')
'''
parser.add_argument('naive')
parser.add_argument('loudness')
parser.add_argument('-v', action='store_true')
parser.add_argument('-p', action='store_true')
'''
parser.add_argument('tunes')
parser.add_argument('output')
args = parser.parse_args()

tunes_dir = args.tunes
output_dir = args.output

naive_perc = 0.25   #float(args.naive)
loudness_perc = 1   #float(args.loudness)
vibrato_on = False  #args.v
do_plots = False    #args.p
plot_path = f'{output_dir}/plots/'


###### directories ######
ALL_MODELS_DIR = './models'

# create non existent dirs
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

if not os.path.exists(plot_path) and do_plots:
    os.makedirs(plot_path)

# get all instruments to render
instruments = os.listdir(tunes_dir)

for i in instruments:
    d = f'{output_dir}/{i}'
    if not os.path.exists(d):
        os.makedirs(d)

###### models ######

# model parameters
CLIP_DURATION = 150
SAMPLE_RATE = 16000
FEATURE_FRAME_RATE = 250

# load all models

print('Loading models...')

# dictionaries containing a list of the model variants for each entry
synthesis_models = {}
control_models = {}

for i in instruments:
    synthesis_models[i] = []
    control_models[i] = []

for i in instruments:
    print(i)

    model_dir = f'{ALL_MODELS_DIR}/{i}'
    synth_dir = f'{model_dir}/synthesis'
    contr_dir = f'{model_dir}/control'

    variants = os.listdir(synth_dir)
    for v in variants:
        st = time.time()

        synthesis_models[i].append(
            get_trained_synthesis_model(f'{synth_dir}/{v}', CLIP_DURATION=CLIP_DURATION))

        et = time.time() - st
        print(f'\t{i}/{v} synth took {et} s')

    variants = os.listdir(contr_dir)
    for v in variants:
        st = time.time()

        c_m = AimuControlModel(n_timesteps=CLIP_DURATION*FEATURE_FRAME_RATE)
        restore(c_m, None, 0, f'{contr_dir}/{v}')
        control_models[i].append(c_m)

        et = time.time() - st
        print(f'\t{i}/{v} control took {et} s')

    print('done')

print('Done')
print('Loading midi files...')

all_midi = {}

# get files to render
# for each instrument
for ins in instruments:
    midi_num = len(os.listdir(f'{tunes_dir}/{ins}'))
    print(f'{ins}: {midi_num} files')
    st = time.time()

    all_midi[ins] = load_midi_examples(midi_dir=f"{tunes_dir}/{ins}",midi_frame_rate=FEATURE_FRAME_RATE,
                                       clip_duration=CLIP_DURATION, voice_limit=1, sample_rate=SAMPLE_RATE)

    et = time.time() - st
    print(f'\t{ins} files took {et} s')
    if midi_num != 0:
        print(f'\t{et/midi_num} s per file')

    print('done')

print('Done')

###### rendering ######

print('Rendering midi files...')

naive_perc = {
    'accordion': 1,
    'fiddle': 0.25,
    'whistle': 0.1
}

for ins in instruments:

    print(ins)

    midi_files = all_midi[ins]
    midi_audio_dict = {}

    for midi_name, demo_batch in midi_files.items():

        print(midi_name)
        st = time.time()
        generated_audio = generate_audio(random.choice(control_models[ins]), random.choice(synthesis_models[ins]),
                                         midi_name + '.png', do_plots, plot_path, demo_batch,
                                         naive_perc[ins], loudness_perc, vibrato_on)
        et = time.time() - st
        print(f'\tPerformance generation took {et} s')

        for k in generated_audio.keys():
            midi_audio_dict[f'{midi_name}_{k}'] = generated_audio[k]

        st = time.time()
        save_audio_from_dict(midi_audio_dict, f'{output_dir}/{ins}', SAMPLE_RATE)
        et = time.time() - st
        print(f'\tSaving took {et} s')

    print('done')

print('Done')


