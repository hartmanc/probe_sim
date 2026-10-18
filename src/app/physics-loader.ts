// Selects the physics implementation. `?stub=1` always uses the kinematic stub.
//
// TODO(integrator): src/physics did not exist when the app was written, so the
// "real" import below points at the stub. Once src/physics/index.ts exists,
// change this ONE line to:   import * as real from '../physics';
import * as real from '../physics';
import * as stub from './physics-stub';
import type { PhysicsApi } from './physics-types';

const params = new URLSearchParams(location.search);
export const usingStub = params.get('stub') === '1' || (real as unknown) === (stub as unknown);

export const physics: PhysicsApi = params.get('stub') === '1' ? stub : real;
