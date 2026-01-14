from params.general_params import *
from subsystems.simulator import TtsPidSim
from common.utils import set_default_params

system = TtsPidSim(tp, pr)

set_default_params(system)

tend = 1000
for i in range(int(tend / tp) + 1):
    rval = system.simulation_step(True)