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
