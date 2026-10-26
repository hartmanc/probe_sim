#!/bin/sh
# usage: tools/calibrate/sweep.sh "<extra drive.ts args>" alat1 alat2 ...
# prints one line per alat: lap time, max lateral error, off-track ms, corner errors vs driver A
extra="$1"; shift
for a in "$@"; do
  npx tsx tools/calibrate/drive.ts $extra --alat "$a" --json --quiet --no-files | node -e '
    let s = ""; process.stdin.on("data", (d) => (s += d)).on("end", () => {
      const j = JSON.parse(s);
      const c = j.corners.map((c) => c.errDriverA.toFixed(0)).join(" ");
      console.log(`alat ${j.alat}: ${j.complete ? "ok " : "BAD"} lap ${j.lapTime.toFixed(2)} maxErr ${j.maxLatErr.toFixed(1)} off ${j.offTrackSteps} | s300 ${j.front.sim.toFixed(1)} | corner % vs driver A: ${c}`);
    });'
done
