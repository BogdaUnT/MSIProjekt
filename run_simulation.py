from params.general_params import *
from subsystems.simulator import TtsPidSim
from common.utils import set_default_params

import random
import numpy as np

""" system = TtsPidSim(tp, pr)

set_default_params(system)



tend = 1000
#proc_vars = system.simulate(tend, True, True)
proc_vars = system.simulate(tend, 'monit', True)
"""

# ======================================================
# PARAMETRY
# ======================================================

TEND = 800
LOG_MODE = 'monit'

POP_SIZE = 20
N_GEN = 20
MUT_PROB = 0.3

KE_RANGE = (0.2, 5.0)
KDE_RANGE = (0.001, 0.05)
KDCV_RANGE = (0.5, 5.0)


def set_defaults_pid(system):
    system.in_var_val('distEnable', 0)
    system.in_var_val('kp', 10)
    system.in_var_val('Ti', 15)
    system.in_var_val('Td', 5)
    system.in_var_val('Bias', 50)
    system.in_var_val('Ienable', 1)
    system.in_var_val('Denable', 1)
    system.in_var_val('PIDmode', 0)


def set_defaults_fuzzy(system):
    system.in_var_val('distEnable', 0)
    system.in_var_val('ke', 1.0)
    system.in_var_val('kde', 0.01)
    system.in_var_val('kdCV', 1.0)


# ======================================================
# FUNKCJA CELU
# ======================================================

def cost_function(params):
    ke, kde, kdCV = params

    system = TtsPidSim(tp, pr, _use_fuzzy_control=True)
    set_defaults_fuzzy(system)

    system.in_var_val('ke', ke)
    system.in_var_val('kde', kde)
    system.in_var_val('kdCV', kdCV)

    data = system.simulate(TEND, 'monit', False)

    e = np.array(data['e'])

    # === FUNKCJA CELU ===
    # ISE – całka z kwadratu odchyłki
    J = np.sum(e ** 2)

    # kara za oscylacje
    J += 0.1 * np.sum(np.abs(np.diff(e)))

    return J


# ======================================================
# ALGORYTM EWOLUCYJNY
# ======================================================

def random_individual():
    return [
        random.uniform(*KE_RANGE),
        random.uniform(*KDE_RANGE),
        random.uniform(*KDCV_RANGE)
    ]


def mutate(ind):
    if random.random() < MUT_PROB:
        ind[0] = random.uniform(*KE_RANGE)
    if random.random() < MUT_PROB:
        ind[1] = random.uniform(*KDE_RANGE)
    if random.random() < MUT_PROB:
        ind[2] = random.uniform(*KDCV_RANGE)
    return ind


def crossover(p1, p2):
    a = random.random()
    return [
        a * p1[0] + (1 - a) * p2[0],
        a * p1[1] + (1 - a) * p2[1],
        a * p1[2] + (1 - a) * p2[2]
    ]


def evolutionary_tuning():
    print("START evolutionary_tuning")
    population = [random_individual() for _ in range(POP_SIZE)]

    best = None
    best_cost = float('inf')

    for gen in range(N_GEN):
        scored = [(cost_function(ind), ind) for ind in population]
        scored.sort(key=lambda x: x[0])

        if scored[0][0] < best_cost:
            best_cost = scored[0][0]
            best = scored[0][1]

        print(f"Gen {gen+1}: J = {scored[0][0]:.3f}")

        elite = [ind for _, ind in scored[:POP_SIZE // 3]]
        new_pop = elite.copy()

        while len(new_pop) < POP_SIZE:
            p1, p2 = random.sample(elite, 2)
            child = crossover(p1, p2)
            new_pop.append(mutate(child))

        population = new_pop

    print("END evolutionary_tuning")
    return best, best_cost


# ======================================================
# PORÓWNANIE REGULATORÓW
# ======================================================

def run_pid():
    sys = TtsPidSim(tp, pr, _use_fuzzy_control=False)
    set_defaults_pid(sys)
    return sys.simulate(TEND, 'monit', False)


def run_fuzzy_manual():
    sys = TtsPidSim(tp, pr, _use_fuzzy_control=True)
    set_defaults_fuzzy(sys)
    return sys.simulate(TEND, 'monit', False)


def run_fuzzy_auto(params):
    sys = TtsPidSim(tp, pr, _use_fuzzy_control=True)
    set_defaults_fuzzy(sys)

    sys.in_var_val('ke', params[0])
    sys.in_var_val('kde', params[1])
    sys.in_var_val('kdCV', params[2])

    return sys.simulate(TEND, 'monit', False)
# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    best_params, best_cost = evolutionary_tuning()

    print("\n=== NAJLEPSZE PARAMETRY FUZZY ===")
    print(f"ke   = {best_params[0]:.3f}")
    print(f"kde  = {best_params[1]:.4f}")
    print(f"kdCV = {best_params[2]:.3f}")
    print(f"J    = {best_cost:.3f}")

    pid_data = run_pid()
    fuzzy_manual = run_fuzzy_manual()
    fuzzy_auto = run_fuzzy_auto(best_params)