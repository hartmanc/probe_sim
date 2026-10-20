"""Heights from pixel measurements on a Street View panorama, an onboard frame or a satellite capture's shadows
(tools/track/compare/HEIGHTS.md has the method, the known sizes and one worked example per kind).

Image rows are measured downward from the top of the image, in the same pixels for every argument. The camera is
assumed level (Street View with pitch 0: the horizon is the middle row of the view; an onboard frame: the vanishing
point of the straight road or the far horizon). Pinhole model: tan(angle below the horizon) = (row - horizon) / f,
f = (image height / 2) / tan(vertical FOV / 2).

    python3 -I tools/track/inventory/heights.py horizon --top 366 --bottom 459 --horizon 414.5 --cam 2.5
    python3 -I tools/track/inventory/heights.py ref --top 355 --bottom 527 --ref-top 492 --ref-bottom 527 --ref-h 0.81
    python3 -I tools/track/inventory/heights.py camh --ref-top 492 --ref-bottom 527 --horizon 460 --ref-h 0.81
    python3 -I tools/track/inventory/heights.py shadow --len 6.2 --lat 38.161 --lon -122.455 --utc 2025-06-14T19:30
    python3 -I tools/track/inventory/heights.py dist --bottom 459 --horizon 414.5 --cam 2.5 --img-h 829 --vfov 72

Standard library only.
"""
import argparse
import datetime as dt
import math
import sys

# known sizes (m), HEIGHTS.md
KNOWN = {
    'jersey': 0.81,          # concrete Jersey barrier (32 in)
    'safer': 1.15,           # SAFER / pit wall, 1.1-1.2
    'catch_fence_post': 3.5,  # catch-fence posts 3-4 (curved top included)
    'cone': 0.70,            # 28 in traffic cone (the 18 in cone is 0.46)
    'cone_small': 0.46,
    'formula_car': 0.90,     # open-wheel car, roll hoop
    'person': 1.70,
    'door': 2.03,            # US standard door, 80 in
    'tyre_layer': 0.21,      # one passenger tyre lying flat in a stack
    'storey': 3.2,           # one storey of a building (3.0-3.5)
    'streetview_cam': 2.5,   # Google car-mounted rig
}


def focal_px(img_h, vfov_deg):
    return (img_h / 2.0) / math.tan(math.radians(vfov_deg) / 2.0)


def height_horizon(top_row, bottom_row, horizon_row, cam_h):
    """Height of a vertical object standing on the camera's ground plane, from its top and base rows and the horizon
    row: h = cam_h * (base - top) / (base - horizon). Exact for a level pinhole camera (the focal length cancels);
    the base must be visible and on the same level as the camera's ground."""
    db = bottom_row - horizon_row
    if db <= 0:
        raise ValueError('the base must be below the horizon (bottom_row > horizon_row)')
    return cam_h * (bottom_row - top_row) / db


def distance_horizon(bottom_row, horizon_row, cam_h, img_h, vfov_deg):
    """Ground distance to the object's base: d = cam_h * f / (base - horizon)."""
    return cam_h * focal_px(img_h, vfov_deg) / (bottom_row - horizon_row)


def height_reference(top_row, bottom_row, ref_top_row, ref_bottom_row, ref_h):
    """Height by proportion to a reference of known size at the same distance (same base row, or a reference standing
    against the object): h = ref_h * (base - top) / (ref_base - ref_top)."""
    return ref_h * (bottom_row - top_row) / (ref_bottom_row - ref_top_row)


def camera_height(ref_top_row, ref_bottom_row, horizon_row, ref_h):
    """Camera height from a reference of known size standing on the ground: inverse of height_horizon."""
    return ref_h * (ref_bottom_row - horizon_row) / (ref_bottom_row - ref_top_row)


def height_angles(top_row, bottom_row, horizon_row, img_h, vfov_deg, dist):
    """Height when the base is not on the camera's ground (a bank, a terrace) but the distance is known from the map:
    h = d * (tan(base angle) - tan(top angle)), angles below the horizon positive."""
    f = focal_px(img_h, vfov_deg)
    return dist * ((bottom_row - horizon_row) - (top_row - horizon_row)) / f


def sun_elevation(lat, lon, when_utc):
    """Solar elevation (deg) at lat/lon (deg, east positive) and a UTC datetime; NOAA solar position equations
    (accuracy ~0.1 deg, ample for shadow lengths)."""
    d = when_utc
    doy = d.timetuple().tm_yday
    hour = d.hour + d.minute / 60 + d.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                    - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour * 60 + eqt + 4 * lon            # true solar time, minutes
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1.0, min(1.0, cz))))


def height_shadow(shadow_len, sun_elev_deg):
    """Height of a vertical object from the length of its shadow on flat ground."""
    return shadow_len * math.tan(math.radians(sun_elev_deg))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    a = sp.add_parser('horizon'); a.add_argument('--top', type=float, required=True); a.add_argument('--bottom', type=float, required=True)
    a.add_argument('--horizon', type=float, required=True); a.add_argument('--cam', type=float, default=KNOWN['streetview_cam'])
    a = sp.add_parser('ref'); a.add_argument('--top', type=float, required=True); a.add_argument('--bottom', type=float, required=True)
    a.add_argument('--ref-top', type=float, required=True); a.add_argument('--ref-bottom', type=float, required=True)
    a.add_argument('--ref-h', type=float, required=True)
    a = sp.add_parser('camh'); a.add_argument('--ref-top', type=float, required=True); a.add_argument('--ref-bottom', type=float, required=True)
    a.add_argument('--horizon', type=float, required=True); a.add_argument('--ref-h', type=float, required=True)
    a = sp.add_parser('dist'); a.add_argument('--bottom', type=float, required=True); a.add_argument('--horizon', type=float, required=True)
    a.add_argument('--cam', type=float, default=KNOWN['streetview_cam']); a.add_argument('--img-h', type=float, required=True)
    a.add_argument('--vfov', type=float, required=True)
    a = sp.add_parser('angles'); a.add_argument('--top', type=float, required=True); a.add_argument('--bottom', type=float, required=True)
    a.add_argument('--horizon', type=float, required=True); a.add_argument('--img-h', type=float, required=True)
    a.add_argument('--vfov', type=float, required=True); a.add_argument('--dist', type=float, required=True)
    a = sp.add_parser('shadow'); a.add_argument('--len', type=float, required=True); a.add_argument('--lat', type=float, required=True)
    a.add_argument('--lon', type=float, required=True); a.add_argument('--utc', required=True, help='capture time, ISO, UTC')
    r = ap.parse_args(argv)
    if r.cmd == 'horizon':
        print(f'{height_horizon(r.top, r.bottom, r.horizon, r.cam):.2f} m')
    elif r.cmd == 'ref':
        print(f'{height_reference(r.top, r.bottom, r.ref_top, r.ref_bottom, r.ref_h):.2f} m')
    elif r.cmd == 'camh':
        print(f'camera {camera_height(r.ref_top, r.ref_bottom, r.horizon, r.ref_h):.2f} m above the ground')
    elif r.cmd == 'dist':
        print(f'{distance_horizon(r.bottom, r.horizon, r.cam, r.img_h, r.vfov):.1f} m to the base')
    elif r.cmd == 'angles':
        print(f'{height_angles(r.top, r.bottom, r.horizon, r.img_h, r.vfov, r.dist):.2f} m')
    elif r.cmd == 'shadow':
        when = dt.datetime.fromisoformat(r.utc)
        el = sun_elevation(r.lat, r.lon, when)
        print(f'sun {el:.1f} deg -> {height_shadow(r.len, el):.2f} m')
    return 0


if __name__ == '__main__':
    sys.exit(main())
