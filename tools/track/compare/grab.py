"""grab.py NAME FILE T [OUT] - full-res windscreen crop of an onboard frame (1220x305 from 1920x1080)."""
import subprocess, sys
V = '/Users/cobyhartman/projects/starlink-go-pro/video/proxies/'
CROP = 'crop=1220:305:280:395'
def grab(f, t, out, w=1220):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', V + f + '.LRV', '-frames:v', '1', '-vf', f'{CROP},scale={w}:-1', '-q:v', '3', out], check=True)
if __name__ == '__main__':
    grab(sys.argv[1], float(sys.argv[2]), sys.argv[3])
