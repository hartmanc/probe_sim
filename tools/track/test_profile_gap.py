"""A deck misclassified as ground must not become the road's crest or banking."""
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import profile_gap as PG
import centre


def fixture():
    n = 240
    C = np.c_[np.arange(n, dtype=float), np.zeros(n)]
    lat = np.tile(-np.asarray(centre.B.FRACTIONS)*6, (n, 1))
    s = np.arange(n, dtype=float)
    truth = 3 + .012*s[:, None] + .00001*s[:, None]**2 + .025*lat + .0004*lat**2
    w = PG.windows(C, [dict(latlon=(120, 0), half_m=15, fit_m=7,
                           src='synthetic measured deck footprint', why='occluded road')], lambda x,y:(x,y))
    return C, lat, truth, w


def test_gap_uses_clean_end_heights_and_slopes_preserving_banking():
    C, lat, truth, wins = fixture()
    corrupt = truth.copy(); corrupt[110:131] += 4 + np.linspace(0, .8, 7)
    repaired = PG.repair(corrupt, wins, lambda *a:None)
    assert np.max(np.abs(repaired-truth)) < .001
    assert np.max(np.abs(np.diff(repaired, axis=0))) < .02
    assert np.allclose(repaired[:105], corrupt[:105])
    assert np.allclose(repaired[136:], corrupt[136:])
    # The reconstructed cross-slope is still the measured 2.5%, never flat.
    assert np.allclose((repaired[120,0]-repaired[120,-1])/12, .025)


def test_gap_heightfield_continues_the_banked_road_and_fades_outside():
    C, lat, truth, wins = fixture()
    box=(0.,-20.,239.,20.); dx=1.
    x,y=np.meshgrid(np.arange(240.), np.arange(-20.,21.))
    ground=3+.012*x+.00001*x**2+.025*y+.0004*y**2
    raw=ground.copy();raw[(x>=110)&(x<=130)&(np.abs(y)<=8)]+=4
    fixed=PG.heightfield(raw, box, dx, C, np.full(240,6.), np.full(240,6.), truth, wins)
    assert np.max(np.abs(fixed[14:27,110:131]-ground[14:27,110:131])) < 1e-10
    assert np.array_equal(fixed[:,0:100],raw[:,0:100])
    assert np.array_equal(fixed[:5],raw[:5])
    assert np.max(np.abs(np.diff(fixed[20,100:141]))) < .02


def test_empty_opt_in_is_byte_identical():
    C,lat,truth,wins=fixture()
    out=PG.repair(truth, [],lambda *a:None)
    assert out.tobytes()==truth.tobytes()
    hf=np.arange(100,dtype='<f4').reshape(10,10)
    assert PG.heightfield(hf,(0,0,9,9),1,C,np.ones(240),np.ones(240),truth,[]) is hf


def test_ground_deck_samples_are_not_used_for_lidar_correction(tmp_path):
    # Correct ground lies 10cm above the DEM; a misclassified 90cm-high deck
    # would pass the legacy 1m max-correction filter unless the interval is masked.
    n=80;x=np.arange(n,dtype=float); z=np.where((x>=30)&(x<=50), .9,.1)
    # Three nearby class-2 returns at each station provide a valid median.
    cache=tmp_path/'points.npz'
    np.savez(cache,x=np.repeat(x,3),y=np.tile([-.05,0,.05],n),
             z=np.repeat(z,3),c=np.full(3*n,2))
    old=centre.LIDAR_POINTS;centre.LIDAR_POINTS=str(cache)
    try:
        out=centre.lidar_correct(x[:,None],np.zeros((n,1)),np.zeros((n,1)),0,
                                 ignore_stations=(x>=28)&(x<=52))
    finally:centre.LIDAR_POINTS=old
    assert np.max(np.abs(out-.1)) < 1e-12


def test_fractional_station_surface_on_curved_graded_road():
    # A nonaligned 70cm heightfield exposes nearest-station staircases.
    from geo import left_normals, FRACTIONS
    n=300
    theta=np.linspace(0,2*np.pi,n,endpoint=False)
    C=np.c_[.3+50*np.cos(theta),.3+50*np.sin(theta)]
    nl=left_normals(C);lat=-np.asarray(FRACTIONS)*6
    xy=C[:,None,:]+lat[None,:,None]*nl[:,None,:]
    prof=2+.02*xy[:,:,0]+.03*xy[:,:,1]
    wins=PG.windows(C,[dict(latlon=tuple(C[70]),half_m=12,fit_m=7,
                           src='test footprint',why='occluded bridge')],lambda x,y:(x,y))
    box=(-60.,-60.,60.,60.);dx=.7
    x,y=np.meshgrid(-60+np.arange(173)*dx,-60+np.arange(173)*dx)
    ground=2+.02*x+.03*y
    raw=ground.copy();bad=(abs(x-C[70,0])<5)&(abs(y-C[70,1])<5);raw[bad]+=4
    fixed=PG.heightfield(raw,box,dx,C,np.full(n,6.),np.full(n,6.),prof,wins)
    assert np.max(np.abs(fixed[bad]-ground[bad])) < .002
    # Difference from the true plane has no repeated station-sized steps.
    assert np.max(np.abs(np.diff((fixed-ground)[bad.any(axis=1)],axis=1))) < .002


def test_invalid_gap_dimensions_fail():
    import pytest
    C,_,_,_=fixture()
    for key,val in [('half_m',float('nan')),('fit_m',0),('lateral_fade',0)]:
        r=dict(latlon=(120,0),half_m=15,fit_m=7,src='test',why='test');r[key]=val
        with pytest.raises(ValueError,match='positive and finite'):
            PG.windows(C,[r],lambda x,y:(x,y))
