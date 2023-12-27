# modified parser based on https://gist.github.com/frumpy4/9c73451ca5593273578729d0eba83517 by frumpy4

import re
import csv

re_res = re.compile(r"^[ \t] *Resolution.*?(\d+)")
re_bpm = re.compile(r"^[ \t] *(\d+) = B (\d+)")
re_ts = re.compile(r"^[ \t] *(\d+) = TS (\d+)")
re_difficulty = re.compile(r"\[([a-zA-Z0-9_]+)\]")
re_note = re.compile(r"^[ \t]*(\d+) = N (\d+) (\d+)")
re_special = re.compile(r"^[ \t]*(\d+) = S (\d+) (\d+)")

resolution = None
markers = []

song_folder_path = "songs/"
song_folder_name = "Through the Fire and Flames"
fp = song_folder_path + song_folder_name + "/notes.chart"

counter = 0
lead_guitar_difficulty_dict = {}
last_difficulty = None
with open(fp, encoding="utf8") as f:
    for line in f:
        m = re_res.match(line)
        if m:
            resolution = int(m.group(1))
            continue

        m = re_ts.match(line)
        if m:
            markers.append(("TS", int(m.group(1)), int(m.group(2))))
            continue

        m = re_bpm.match(line)
        if m:
            markers.append(("B", int(m.group(1)), int(m.group(2))))
            continue

        m = re_difficulty.match(line)
        if m:
            print(m)
        if m and "Single" in m.group(0):
            print(m.group(1))
            last_difficulty = m.group(1)
        if m and not "Single" in m.group(0):
            print(m.group(1))
            last_difficulty = None

        m = re_note.match(line)
        print([line], re_note.match(line))
        if m and last_difficulty:
            # print(m.group(1), "N", m.group(2), m.group(3))
            print(m)
            if last_difficulty not in lead_guitar_difficulty_dict:
                tick, lane, length = m.group(1), m.group(2), m.group(3)
                lead_guitar_difficulty_dict[last_difficulty] = [(int(tick), "N", int(lane), int(length))]
            else:
                tick, lane, length = m.group(1), m.group(2), m.group(3)
                lead_guitar_difficulty_dict[last_difficulty].append((int(tick), "N", int(lane), int(length)))

        m = re_special.match(line)
        if m and last_difficulty:
            # print(m.group(1), "S", m.group(2), m.group(3))
            if last_difficulty not in lead_guitar_difficulty_dict:
                tick, type, length = m.group(1), m.group(2), m.group(3)
                lead_guitar_difficulty_dict[last_difficulty] = [(int(tick), "S", type, int(length))]
            else:
                tick, type, length = m.group(1), m.group(2), m.group(3)
                lead_guitar_difficulty_dict[last_difficulty].append((int(tick), "S", type, int(length)))

for key in lead_guitar_difficulty_dict:
    print("hello", key)
    print(key, len(lead_guitar_difficulty_dict[key]))

print(lead_guitar_difficulty_dict[key][:20])
#
# print(lead_guitar_difficulty_dict["HardSingle"] == lead_guitar_difficulty_dict["MediumSingle"])



if resolution is None:
    print("could not find chart resolution")
    exit(1)

def bpm_to_length(bpm):
     # beats per minute / 60 = beats per second
     # 1 / bps = seconds per beat * 1000 = ms per beat
    return 1 / (bpm/60) * 1000

timing_fmt = "{time},{bpm},{beatLength},{meter},{sampleSet},{sampleIndex},{volume},{uninherited},{effects}"
def osu_timing(t, bpm, ts):
    return (t , bpm)

ts = 4
time = 0

last_bpm = 0
last_beat = 0


bpm_marker_list = [(m[1], m[0], m[2]/1000) for m in markers if m[0] == "B"]
print(bpm_marker_list)
bpm_timing_list = []
for m in markers:
    if m[0] == "TS":
        ts = m[2]
        continue

    # resolution is how many ticks are in a beat
    # beat length can vary but tick count doesn't, so each tick length can vary
    # this means there's no actual timing information in marker location
    # we have to calculate actual time iteratively

    bpm = m[2] / 1000

    # dividing the marker location by resolution gets the beat the marker was placed at
    # markers can be placed in the middle of beats so this is not an integer
    beat = m[1] / resolution

    # uncomment to generate a timing point for the initial bpm marker
    # this may or not be necessary
    # calculating the time without previous markers is impossible, but it's always 0 anyways..
    if beat == 0:
        bpm_timing_list.append(osu_timing(0, bpm, ts))

    if beat != 0:
        # how many beats have passed since the last bpm marker
        beat_length = beat - last_beat

        # bpm / 60 = beats per second; 1 / bps = seconds per beat
        # multiplied by beat_length = actual time (in seconds) since last bpm marker
        t = beat_length * (1 / (last_bpm / 60))

        time += t
        bpm_timing_list.append(osu_timing(time, bpm, ts))

    last_beat = beat
    last_bpm = bpm

print(bpm_timing_list)

def notes_converter_ticks_to_seconds(notes_list, bpm_marker_list, bpm_timing_list):
    current_note_index = 0
    current_bpm_index = 0

    return_list = []
    while current_note_index < len(notes_list):
        current_note_tick = notes_list[current_note_index][0]

        current_bpm = bpm_marker_list[current_bpm_index][2]

        current_bpm_tick = bpm_marker_list[current_bpm_index][0]

        current_bpm_time = bpm_timing_list[current_bpm_index][0]

        if current_bpm_index + 1 < len(bpm_marker_list):
            next_bpm = bpm_marker_list[current_bpm_index + 1][2]
            next_bpm_tick = bpm_marker_list[current_bpm_index + 1][0]
            next_bpm_time = bpm_timing_list[current_bpm_index + 1][0]
        else:
            next_bpm_tick = current_note_tick

        if current_note_tick <= next_bpm_tick:
            seconds_per_beat = 60 / current_bpm
            delta_ticks = current_note_tick - current_bpm_tick
            delta_beat = delta_ticks/resolution
            delta_seconds = seconds_per_beat * delta_beat
            seconds = delta_seconds + current_bpm_time

            if seconds >=0:
                return_list.append((seconds, notes_list[current_note_index][1], int(notes_list[current_note_index][2]), (notes_list[current_note_index][3]/resolution)*seconds_per_beat))
            current_note_index += 1
        else:
            current_bpm_index += 1

    return return_list
print(lead_guitar_difficulty_dict.keys())
val = notes_converter_ticks_to_seconds(lead_guitar_difficulty_dict["ExpertSingle"], bpm_marker_list, bpm_timing_list)

map_bpm = bpm_marker_list[0][2]
seconds = val[-1][0]
print(seconds)
print(map_bpm)
beats_per_second = map_bpm/60
print(beats_per_second)
number_of_beats = int(seconds*beats_per_second)
print(number_of_beats)
beat_marker_list = []

for i in range(number_of_beats):
    beat_marker_list.append((val[0][0] + i*(1/beats_per_second), "B", 0, 0))

print(val)
val = sorted(val, key=lambda x: x[2], reverse=True)
val = sorted(val, key=lambda x: round(x[0], 3))

val = beat_marker_list + val

with open(song_folder_path + song_folder_name + "/notes.tsv", 'w', newline='') as tsvfile:
    writer = csv.writer(tsvfile, delimiter='\t', lineterminator='\n')
    for note in val:
        writer.writerow([round(note[0], 3), note[1], note[2], note[3]])



