"""Yellow kerbs are opt-in evidence, not mistaken for an absent white line."""
import os,sys
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import edges_spline as E


def test_continuous_yellow_kerb_outer_limit_and_default_inertness():
    u=E.U
    v=np.tile([160.,160.,160.],(len(u),1))
    v[(u>=0)&(u<1)]=[230,220,65]
    v[u>=1]=[65,95,55]
    valid=np.ones(len(u),bool)
    assert E.bands(v,valid)==[]
    bands=E.bands(v,valid,yellow=True)
    assert len(bands)==1
    assert abs(bands[0][1]-1)<.06 and bands[0][2]


def test_grass_without_inner_asphalt_is_not_a_yellow_kerb():
    v=np.tile([150.,160.,70.],(len(E.U),1))
    assert E.bands(v,np.ones(len(v),bool),yellow=True)==[]


def test_inner_kerb_convention_uses_track_facing_band_for_all_colours():
    # Width varies by kerb: use the measured band, never subtract a rule width.
    for lo,hi,red in [(-1.2,-.4,True),(.1,1.4,True),(-.3,.8,False)]:
        band=[(lo,hi,red,hi-lo)]
        assert E.candidates(band,.26,True)==[(hi,2)]
        assert E.candidates(band,.26,True,kerb_edge='inner')==[(lo,2)]
        if red:
            assert E.candidates(band,.26,False,kerb_edge='inner')==[(lo,2)]
    # Plain edge lines keep their existing offset under either convention.
    painted=[(.12,.24,False,.12)]
    assert E.candidates(painted,.26,False)==E.candidates(painted,.26,False,kerb_edge='inner')
    # Yellow evidence feeds the same measured-band convention.
    v=np.tile([160.,160.,160.],(len(E.U),1));v[(E.U>=0)&(E.U<1)]=[230,220,65];v[E.U>=1]=[65,95,55]
    band=E.bands(v,np.ones(len(v),bool),yellow=True)
    assert abs(E.candidates(band,.26,True,'inner')[0][0])<.04
    assert abs(E.candidates(band,.26,True)[0][0]-1)<.06
