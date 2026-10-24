import json
import librosa

AUDIO = r"D:\收集\爱剪辑\临时\自娱自乐\new\分片\项目四\BGM\sexy girl (Remaster).mp3"

y, sr = librosa.load(AUDIO, sr=44100, mono=True)
duration = librosa.get_duration(y=y, sr=sr)

# tempo & beats
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# estimate beat interval regularity
import statistics
iv = [b - a for a, b in zip(beat_times, beat_times[1:])]
med = statistics.median(iv)

print(f"duration: {duration:.2f}s")
import numpy as np
tempo = float(np.atleast_1d(tempo)[0])
print(f"tempo: {tempo:.2f} BPM")
print(f"beats: {len(beat_times)}")
print(f"median interval: {med:.3f}s")
print(f"interval stdev: {statistics.pstdev(iv):.3f}s")
print("first 20 beats:", [round(t, 3) for t in beat_times[:20]])
print("last 5 beats:", [round(t, 3) for t in beat_times[-5:]])

json.dump(
    {"duration": duration, "tempo": float(tempo), "beats": [float(t) for t in beat_times]},
    open("analysis.json", "w", encoding="utf-8"),
)
