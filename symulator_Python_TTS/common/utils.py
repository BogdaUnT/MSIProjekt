import sys
import math

def progress_bar(_t, _end, _steps=100, _length=40):
    if (int(_t)-1) % _steps == 0:
        progress = _t / _end
        bar = '=' * int(_length * progress) + '-' * (_length - int(_length * progress))
        sys.stdout.write(f"\r|{bar}| {int(progress * 100)}%")
        sys.stdout.flush()

def set_default_params(_system):
    _system.in_var_val('distEnable', 0)
    _system.in_var_val('kp', 10)
    _system.in_var_val('Ti', 15)
    _system.in_var_val('Td', 5)
    _system.in_var_val('Bias', 50)
    _system.in_var_val('Ienable', 1)
    _system.in_var_val('Denable', 1)

def set_modes(_system, _sp_mode, _sp_man=0.2, _pid_mode=0, _cv_mode=1, _cv_man=0):
    # SP mode:
    #  1- manual
    #  2- steps in the whole range
    #  3- steps in working point (0.2)
    #  4- sinusoidal
    _system.in_var_val('SPmode', _sp_mode)
    _system.in_var_val('SPman', _sp_man)
    # PID mode:
    #  0 - auto
    #  1 - manual
    _system.in_var_val('PIDmode', _pid_mode)
    # CV mode:
    #  1- manual
    #  2- triangle
    _system.in_var_val('CVmode', _cv_mode)
    _system.in_var_val('CVman', _cv_man)

def filter_FOI(_k, _T, _tp, _x):
    filt_k = _k
    filt_T = _T
    filt_a1 = math.exp(-_tp/filt_T)
    filt_b0 = filt_k*(1-filt_a1)

    y = []
    y.append(_x[0])
    for i in range(1, len(_x)):
        y.append( filt_b0*_x[i-1] + filt_a1*y[i-1] )

    return y

"""
    Obliczanie podstawowych wskaźników jakości regulacji dla podanego przebiegu
    
    @param _tp Okres próbkowania
    @param _sp Lista wartości zadanych
    @param _t Lista wartości czasu
    @param _e Lista wartości odchyłki

    @return Słownik wskaźników jakości regulacji {czas regulacji, odchyłka statyczna, ISE, IAE}
"""
def calculate_quality_indicators(_tp, _t, _sp, _e):
    # Czas regulacji (przyjmujemy tolerancję 2% wartości zadanej)
    settling_time = None
    tolerance = 0.02 * _sp  # 2% wartości zadanej na końcu symulacji
    stable_region_start = None
    # Szukamy momentu, od którego sygnał pozostaje w tolerancji
    for i in range(len(_t) - 1, -1, -1):
        if abs(_e[i]) > tolerance:
            stable_region_start = i + 1  # Czas regulacji jest po ostatnim przekroczeniu tolerancji
            break
    if stable_region_start is not None and stable_region_start < len(_t):
        settling_time = _t[stable_region_start]
    else:
        settling_time = math.inf
    # Odchyłka statyczna (różnica między wartością zadaną a wyjściową w stanie ustalonym)
    # Przyjmujemy ostatnią wartość jako stan ustalony
    static_error = _e[-1]
    # Całka z kwadratu odchyłki (ISE - Integral Squared Error)
    ise = sum([e ** 2 * _tp for e in _e])
    # Całka z wartości bezwzględnej odchyłki (IAE - Integral Absolute Error)
    iae = sum([abs(e) * _tp for e in _e])
    return {
        "st": settling_time,
        "se": static_error,
        "ISE": ise,
        "IAE": iae
    }

from matplotlib import pyplot as plt

"""
    Wyświetla przebiegi i wskaźniki podsumowujące jakośc regulacji:
        - wykres SP i PV
        - wykres e
        - wykres CV

    @param _t Lista wartości czasu
    @param _sp Lista wartości zadanych
    @param _pv Lista wartości wielkości regulowanej
    @param _e Lista wartości odchyłki
    @param _cv Lista wartości sygnału sterującego
    @param _eval Wynik evaluacji z funkcji calculate_quality_indicators(). Domyślnie: None
    @param _elim Dodatkowe ograniczenie progowe do narysowania na przebiegu e. Domyślnie: None 
    @param _splim Lista granic do narysowania na przebiegu SP. Domyślnie: None 
    @param _pv_bis Lista drugich wartości wielkości PV, np. odtwaranych z modelu 
"""
def show_evaluation(_t, _sp, _pv, _e, _cv, _eval=None, _elim=None, _splim=None, _pv_bis=None):
    plt.figure()
    fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(9, 15))

    SP_H = [x + 0.02 for x in _sp]
    SP_L = [x - 0.02 for x in _sp]

    limSP_H = [x * 0.02 for x in _sp]
    limSP_L = [x * (-0.02) for x in _sp]

    ax[0].plot(_t, _sp, label='SP', color='r')
    ax[0].plot(_t, _pv, label='PV', color='g')
    if _pv_bis is not None:
        ax[0].plot(_t, _pv_bis, label='PV_pred', color='palegreen')
    ax[0].plot(_t, SP_H, linestyle='', marker='.', markersize=2, label='2%', color='b', )
    ax[0].plot(_t, SP_L, linestyle='', marker='.', markersize=2, color='b')
    ax[0].legend()
    if _eval is not None:
        ax[0].set_title(f"st: {_eval['st']:.2f}")
    if _splim is not None:
        for pos, v in enumerate(_splim):
            ax[0].plot([0, _t[-1]], [_splim[pos], _splim[pos]], label=('lim' if pos==0 else ''), color='y')

    ax[1].plot(_t, _e, label='e', color='g')
    ax[1].plot(_t, limSP_H, linestyle='', marker='.', markersize=2, label='2%', color='b')
    ax[1].plot(_t, limSP_L, linestyle='', marker='.', markersize=2, color='b')
    if _elim is not None:
        ax[1].plot([0, _t[-1]], [_elim, _elim], label='lim', color='y')
        ax[1].plot([0, _t[-1]], [-_elim, -_elim], color='y')
    ax[1].legend()
    if _eval is not None:
        ax[1].set_title(f"ISE: {_eval['ISE']:.3f}")

    ax[2].plot(_t, _cv, label='CV', color='g')
    ax[2].legend()