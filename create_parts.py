import os
import time
import argparse
import random

import repeat_midi
import abc_spicer
import stomping
import microtiming
import mixer

# args
parser = argparse.ArgumentParser(description='Generate and render individual instrument parts for folk tunes')
parser.add_argument('input', help='Folder with the files to process')
parser.add_argument('output', help='Output folder for midi and audio')
args = parser.parse_args()

# dirs
input_dir = args.input
files = os.listdir(input_dir)
output_dir = os.path.abspath(args.output)

midi_output_dir = f'{output_dir}/midi'
audio_output_dir = f'{output_dir}/audio'
song_output_dir = f'{output_dir}/songs'
stomp_output_dir = f'{audio_output_dir}/stomps'
tmp_dir = f'{output_dir}/tmp'

os.makedirs(tmp_dir)

# instruments
instr_list = ['fiddle', 'whistle', 'accordion']

for i in instr_list:
    os.makedirs(f'{midi_output_dir}/{i}')

st = time.time()

tempo = 112

# for each file
for file in files:

    # random arrangement
    number = random.randint(3, 5)
    parts = random.choices(instr_list, k=number)
    spices = [round(random.uniform(0, 1), 3) for _ in range(number)]
    tempo += 8

    # spice abc
    print(file)
    for i in range(number):
        print(f'Generating part {i}: {parts[i]} with spice {spices[i]}')
        repeat_midi.main(f'{input_dir}/{file}', 3, f'{tmp_dir}/{file}')
        abc_spicer.main(f'{tmp_dir}/{file}', parts[i], spices[i], tempo, f'{midi_output_dir}/{parts[i]}')
        if i == number-1:
            # generate stomps
            print('Generating stomps')
            stomping.main(f'{tmp_dir}/{file}', tempo, stomp_output_dir)
    print()

# microtiming
for i in instr_list:
    files_to_micro = os.listdir(f'{midi_output_dir}/{i}')
    for file in files_to_micro:
        micro_perc = random.uniform(0.2, 0.3)
        print(f'Generating micro timings for {file} ({micro_perc*100}%)')
        microtiming.main(f'{midi_output_dir}/{i}/{file}', micro_perc, f'{midi_output_dir}/{i}/{file}')
print()

# render with control-synthesis
os.system(f'cd render && python3 midi_render.py {midi_output_dir} {audio_output_dir}')

# mix all tracks
mixer.main(audio_output_dir, False, True, song_output_dir)

et = time.time()-st

os.system(f'rm -fr {tmp_dir}')

print(f'Generation of {len(files)} songs took {et} seconds ({et/len(files)} per file).')




