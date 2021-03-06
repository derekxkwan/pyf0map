# pyf0map
python f0 mapping using pyaapt

detects the fundamental frequency (f0) throughout time of a monophonic input wav using the pyaapt library and uses it to pitchshift a target monophonic wav (code adapted from http://zulko.github.io/blog/2014/03/29/soundstretching-and-pitch-shifting-in-python/ for continuous shifting). If the script detects silences within the input file, it starts the target sound file over again.

The script writes to [inputfilename]-[number].wav.

USAGE:
python pyf0map.py [input] [target]

SAMPLE OUTPUT:
http://freesound.org/people/derekxkwan/sounds/276455/

NOTE: If you get broadcast errors, the target sound is too far from the pitch of the input file and/or too short in length. For best result, use sounds that are not terribly different in pitch register.
