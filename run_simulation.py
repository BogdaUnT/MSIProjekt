from params.general_params import *
from subsystems.simulator import TtsPidSim
from common.utils import set_default_params

import random
import numpy as np

import matplotlib.pyplot as plt
from common.utils import show_evaluation, calculate_quality_indicators

""" system = TtsPidSim(tp, pr)

set_default_params(system)



tend = 1000
#proc_vars = system.simulate(tend, True, True)
proc_vars = system.simulate(tend, 'monit', True)
"""

# ======================================================
# PARAMETRY
# ======================================================

TEND = 300
LOG_MODE = 'monit'

POP_SIZE = 10
N_GEN = 10
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

def plot_fuzzy_membership():
    from fuzzylogic.classes import Domain
    from fuzzylogic.functions import R, S, triangular

    prec = 0.001

    # e
    e_dom = Domain("e", -1, 1, prec)
    e_dom.N = S(-1, 1)
    e_dom.P = R(-1, 1)

    plt.figure()
    e_dom.N.plot()
    e_dom.P.plot()
    plt.title("Zmienna lingwistyczna e")
    plt.legend(["N", "P"])

    # de
    de_dom = Domain("de", -1, 1, prec)
    de_dom.N = S(-1, 1)
    de_dom.P = R(-1, 1)

    plt.figure()
    de_dom.N.plot()
    de_dom.P.plot()
    plt.title("Zmienna lingwistyczna de")
    plt.legend(["N", "P"])

    # dCV
    dcv_dom = Domain("dCV", -1-prec, 1+prec, prec)
    dcv_dom.N = triangular(-1-prec, -1+prec)
    dcv_dom.Z = triangular(-prec, prec)
    dcv_dom.P = triangular(1-prec, 1+prec)

    plt.figure()
    dcv_dom.N.plot()
    dcv_dom.Z.plot()
    dcv_dom.P.plot()
    plt.title("Zmienna lingwistyczna dCV")
    plt.legend(["N", "Z", "P"])


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

    data = system.simulate(TEND, False, False)

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

    # ===== WYKRESY FUNKCJI PRZYNALEŻNOŚCI =====
    plot_fuzzy_membership()

    # ===== PID =====
    eval_pid = calculate_quality_indicators(tp, pid_data['t'], pid_data['SP'][-1], pid_data['e'])
    show_evaluation(
        pid_data['t'], pid_data['SP'], pid_data['PV'], pid_data['e'], pid_data['CV'],
        eval_pid
    )
    plt.suptitle("Regulator PID")

    # ===== FUZZY RĘCZNY =====
    eval_fm = calculate_quality_indicators(tp, fuzzy_manual['t'], fuzzy_manual['SP'][-1], fuzzy_manual['e'])
    show_evaluation(
        fuzzy_manual['t'], fuzzy_manual['SP'], fuzzy_manual['PV'],
        fuzzy_manual['e'], fuzzy_manual['CV'],
        eval_fm
    )
    plt.suptitle("Regulator rozmyty – nastawy ręczne")

    # ===== FUZZY STROJONY =====
    eval_fa = calculate_quality_indicators(tp, fuzzy_auto['t'], fuzzy_auto['SP'][-1], fuzzy_auto['e'])
    show_evaluation(
        fuzzy_auto['t'], fuzzy_auto['SP'], fuzzy_auto['PV'],
        fuzzy_auto['e'], fuzzy_auto['CV'],
        eval_fa
    )
    plt.suptitle("Regulator rozmyty – strojenie ewolucyjne")

    # ===== WYKRES de(t) =====
    plt.figure(figsize=(9, 5))
    plt.plot(fuzzy_auto['t'], fuzzy_auto['de'], label='de')

    kde = best_params[1]
    plt.plot([0, fuzzy_auto['t'][-1]], [kde, kde], 'y--', label='±kde')
    plt.plot([0, fuzzy_auto['t'][-1]], [-kde, -kde], 'y--')

    plt.xlabel("t [s]")
    plt.ylabel("de")
    plt.title("Pochodna odchyłki – regulator rozmyty strojon y")
    plt.legend()
    plt.grid()

    plt.show()