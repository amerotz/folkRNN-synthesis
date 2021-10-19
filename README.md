# folkRNN-synthesis
A synthesis pipeline for machine folk tunes.

# Use
- make the following directories:
  - ```./stomps```, containing individual stomp samples (16k mono)
  - ```./ambiences```, containing ambience sounds (16k mono)
  - ```./impulses```, containing impulse responses
  - ```./render/models```, containing the trained instruments

For each instrument, there should be a folder ```./render/models/<instrument name>```. That folder must contain two folders: ```control```, with the trained control model, and ```synthesis```, with the trained synthesis model.
  
To start the synthesis, call ```create_parts <source midi folder> <destination audio folder>```. The midi files have to be monophonic.
The script will create:
  - ```<dest>/audio```, containining individual wav stems for each instrument
  - ```<dest>/midi```, with the individual microtimed and ornamented midi stems
  - ```<dest>/songs```, with the rendered complete tunes
