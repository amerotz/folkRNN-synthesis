import ddsp
from matplotlib import pyplot as plt
import numpy as np
import tensorflow.compat.v2 as tf
from absl import logging
import time
import librosa

def save_audio_from_dict(audio_dict: dict, save_path: str, SAMPLE_RATE: int):
    for key, value in audio_dict.items():
        librosa.output.write_wav(
            save_path+"/"+key+".wav", np.nan_to_num(tf.squeeze(value[0, ...]).numpy()), SAMPLE_RATE, norm=False)


def generate_audio(control_model, synthesis_model,
                            midi_name, do_plots, plot_export_path, batch,
                            naive_perc, loudness_perc, vibrato_on):

    audio = {}

    generated_performance = generate_performance(control_model, synthesis_model,
                                                                midi_name, do_plots, plot_export_path, batch,
                                                                naive_perc, loudness_perc, vibrato_on)

    generated_performance = tf.math.reduce_sum(generated_performance, axis=0, keepdims=True)
    audio = {**audio, "generated_performance": generated_performance }

    return audio

def generate_performance(
        control_model, synthesis_model,
        midi_name, do_plots, plot_export_path, batch,
        naive_perc, loudness_perc,
        vibrato_on, vibrato_level=0.002, vibrato_hz=5.0,
        resample_ratio=1.0):

    # control model performance
    performance_params = control_model(batch, training=False)
    perf_ld_scaled = performance_params["predicted_ld_scaled"]
    perf_f0_scaled = performance_params["predicted_f0_scaled"]
    perf_f0_hz = ddsp.core.midi_to_hz(perf_f0_scaled*127.0)

    if naive_perc != 0:

        # naive performance
        naive_params = control_model.preprocess(batch)
        naive_ld_scaled = naive_params["midi_velocity_scaled"]
        naive_f0_scaled = naive_params["midi_pitch_scaled"]
        naive_f0_hz = ddsp.core.midi_to_hz(naive_params["midi_pitch_scaled"]*127.0)

    '''
    # resampling
    if resample_ratio < 1.0:

        ld_scaled = ddsp.core.resample(
            ld_scaled, int(ld_scaled.shape[1]*resample_ratio))
        f0_scaled = ddsp.core.resample(
            f0_scaled, int(f0_scaled.shape[1]*resample_ratio))
        f0_hz = ddsp.core.resample(
            f0_hz, int(f0_hz.shape[1]*resample_ratio))
    '''

    ##### pitch #####

    if naive_perc != 0:

        # interpolate between control and naive
        f0_scaled = perf_f0_scaled.numpy()
        f0_orig = f0_scaled.copy()
        f0_scaled *= 1-naive_perc
        f0_scaled += naive_perc*naive_f0_scaled

    # add vibrato
    if vibrato_on:
        MIDI_FRAME_RATE = 250.0
        n_frames = performance_params["predicted_ld_scaled"].shape[1]
        vibrato_unit = tf.math.sin(
            tf.linspace(0.0, n_frames/MIDI_FRAME_RATE, n_frames)*vibrato_hz*2.0*3.14)[None, ..., None]
        vibrato = vibrato_unit*vibrato_level
        f0_scaled += vibrato

    if vibrato_on or naive_perc != 0:
        f0_scaled = tf.convert_to_tensor(f0_scaled)

    else:
        f0_scaled = perf_f0_scaled

    f0_hz = ddsp.core.midi_to_hz(f0_scaled*127.0)

    ##### loudness #####

    if loudness_perc != 1:

        midi_notes = np.copy(batch['midi_pitch'])
        midi_mask = np.copy(batch['midi_pitch'])

        reduce_perc = loudness_perc

        # use midi velocity and midi notes to insert 'pits' in the loudness
        for i in range(len(midi_mask[0])-1):
            if batch['midi_velocity'][0][i] == 0:
                midi_mask[0][i] = reduce_perc
            else:
                midi_mask[0][i] = 1 if midi_notes[0][i] == midi_notes[0][i+1] else reduce_perc
        midi_mask[0][-1] = reduce_perc

        # extend the loudness pit to a few frames ahead
        i = 0
        while i < len(midi_mask[0]):
            if midi_mask[0][i] == reduce_perc:
                j = 0
                while i < len(midi_mask[0]) and j < 5:
                    midi_mask[0][i] = reduce_perc
                    i += 1
                    j += 1
            else:
                i += 1

        # update the generated loudness with the midi mask
        ld_scaled = perf_ld_scaled.numpy()
        ld_orig = ld_scaled.copy()
        ld_scaled *= midi_mask
        ld_scaled = tf.convert_to_tensor(ld_scaled)

    else:
        ld_scaled = perf_ld_scaled

    ##### synthesis #####

    synth_inputs = {
        "ld_scaled": ld_scaled,
        "f0_scaled": f0_scaled,
        "f0_hz":  f0_hz
    }

    if do_plots:
        print('Plotting')
        limit = 2000
        plot_synth_inputs(ld_orig[0][:limit], ld_scaled.numpy()[0][:limit], f0_orig[0][:limit], f0_scaled.numpy()[0][:limit], midi_name, plot_export_path)
        print('Done')

    # generate audio
    performance_audio = synthesis_model.decode(synth_inputs)
    return performance_audio[..., None]

def plot_synth_inputs(ld_orig, ld_sc, f0_orig, f0_sc, midi_name, path):

    fig, axs = plt.subplots(2, 1, figsize=(8,8))

    axs[0].plot(ld_orig)
    axs[0].set_title('Original loudness scaled')
    axs[0].set_xlabel('Time')

    axs[1].plot(ld_sc)
    axs[1].set_title('Edited loudness scaled')
    axs[1].set_xlabel('Time')
    axs[1].set_ylim(min(ld_sc), max(ld_sc))

    fig.tight_layout()
    plt.savefig(fname=f"{path}/LD_{midi_name}")

    fig, axs = plt.subplots(2, 1, figsize=(8,8))

    axs[0].plot(f0_orig)
    axs[0].set_title('Original frequency scaled')
    axs[0].set_xlabel('Time')

    axs[1].plot(f0_sc)
    axs[1].set_title('Edited frequency scaled')
    axs[1].set_xlabel('Time')
    axs[1].set_ylim(min(f0_sc), max(f0_sc))

    fig.tight_layout()
    plt.savefig(fname=f"{path}/F0_{midi_name}")

def restore(model, optimizer, epoch, checkpoint_path):
    """Restore model and optimizer from a checkpoint if it exists."""
    logging.info('Restoring from checkpoint...')
    start_time = time.time()

    # Restore from latest checkpoint.
    checkpoint = ''
    if optimizer is not None:
        checkpoint = tf.train.Checkpoint(model=model, optimizer=optimizer)
    else:
        checkpoint = tf.train.Checkpoint(model=model)

    latest_checkpoint = ddsp.training.train_util.get_latest_chekpoint(
        checkpoint_path)
    if latest_checkpoint is not None:
        # checkpoint.restore must be within a strategy.scope() so that optimizer
        # slot variables are mirrored.
        checkpoint.restore(latest_checkpoint)
        logging.info('Loaded checkpoint %s', latest_checkpoint)
        logging.info('Loading model took %.1f seconds',
                     time.time() - start_time)
        epoch = int(latest_checkpoint.split("ckpt-")[1])
    else:
        logging.info('No checkpoint, skipping.')
        epoch = 0

    return epoch
