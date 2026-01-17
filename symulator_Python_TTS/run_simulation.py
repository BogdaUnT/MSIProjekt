from params.general_params import *
from subsystems.simulator import TtsPidSim
from common.utils import set_default_params

system = TtsPidSim(tp, pr)

set_default_params(system)

tend = 1000
proc_vars = system.simulate(tend, True, True)