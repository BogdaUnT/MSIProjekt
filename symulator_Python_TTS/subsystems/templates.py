from libraries.discontinuities import Limiter, LookupTable1D
from libraries.linear_dynamic import *
from libraries.logic import *
from libraries.math_operations import *
from libraries.signal_routing_and_organize import *
from libraries.sources import *

class Simple1(Subsystem):
    def __init__(self, _name, _inputs):
        super().__init__(_name, _inputs)

        # Add blocks
        gain = self.add_block( Gain('gain', 0.5) )
        gain.add_input(self.input(1))
        sum1 = self.add_block( SumDiff('sum1', [1, 1]) )
        sum1.add_input(self.input(0))
        sum1.add_input(gain.output(0))

        # Add outputs
        self.add_output(sum1.output(0))
        self.add_output(gain.output(0))

class Tank(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): Fin, F1, F2
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp, _asw, _lim, _init):
        super().__init__(_name, _inputs)

        # kw
        asw = self.add_block( Const('asw', _asw) )
        asw_m2 = self.add_block( Gain('asw_m2', 0.0001) )
        asw_m2.add_input(asw.output(0))
        w = self.add_block( Const('w', 0) )
        kw = self.add_block( MulDiv('kw', [1, 1]) )
        kw.add_input(asw_m2.output(0))
        kw.add_input(w.output(0))

        # A
        a = self.add_block( Const('a', 194) )
        a_m2 = self.add_block( Gain('a_m2', 0.0001) )
        a_m2.add_input(a.output(0))

        # Fw
        l2g = self.add_block( Gain('l2g', 19.62) )
        l2gsqrt = self.add_block( Pow('l2gsqrt', 0.5) )
        l2gsqrt.add_input(l2g.output(0))

        fw = self.add_block( MulDiv('fw', [1, 1]) )
        fw.add_input(l2gsqrt.output(0))
        fw.add_input(kw.output(0))

        # Balance
        fin_f1_f2_fw = self.add_block( SumDiff('fin_f1_f2_fw', [1, 1, -1, -1]) )
        fin_f1_f2_fw.add_input(self.input(0))
        fin_f1_f2_fw.add_input(self.input(1))
        fin_f1_f2_fw.add_input(self.input(2))
        fin_f1_f2_fw.add_input(fw.output(0))

        # dL
        dl = self.add_block( MulDiv('dl', [1, -1]) )
        dl.add_input(fin_f1_f2_fw.output(0))
        dl.add_input(a_m2.output(0))

        # Tank
        l = self.add_block( FirstOrderIntegrator('l', _tp, 1, 1, _lim, _init) )
        l.add_input(dl.output(0))

        # Close feedback
        l2g.add_input(l.output(0))

        # Add outputs
        self.add_output(l.output(0))

class Pipe(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): H1, H2
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _asw, _aswh=None):
        super().__init__(_name, _inputs)

        # dH
        dh = self.add_block(SumDiff('dh', [1, -1]))
        dh.add_input(self.input(0))
        dh.add_input(self.input(1))
        dhabs = self.add_block(Abs('dhabs'))
        dhabs.add_input(dh.output(0))
        dhabs2g = self.add_block(Gain('dhabs2g', 2 * 9.81))
        dhabs2g.add_input(dhabs.output(0))
        flow_var = self.add_block(Pow('flow_var', 0.5))
        flow_var.add_input(dhabs2g.output(0))
        flow_dir = self.add_block(Sign('flow_dir'))
        flow_dir.add_input(dh.output(0))
        if _asw is not None:
            asw = self.add_block(Const('asw', _asw))
        else:
            asw = self.add_block( LookupTable1D('asw', 'linear', _aswh[0], _aswh[1]) )
            asw.add_input(dhabs.output(0))
        k = self.add_block(Gain('asw_m2', 0.0001))
        k.add_input(asw.output(0))
        flow = self.add_block(MulDiv('flow', [1, 1, 1]))
        flow.add_input(flow_var.output(0))
        flow.add_input(flow_dir.output(0))
        flow.add_input(k.output(0))

        # Add outputs
        self.add_output(flow.output(0))

class ThreeTanks(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): Fin
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp, _init):
        super().__init__(_name, _inputs)

        # pipes
        zero_l = self.add_block( Const('zero_l', 0) )
        dummy_l1 = self.add_block( Gain('dummy_l1', 1) )
        dummy_l2 = self.add_block( Gain('dummy_l2', 1) )
        dummy_l3 = self.add_block( Gain('dummy_l3', 1) )
        pipe12 = self.add_block( Pipe('pipe12', [dummy_l1.output(0), dummy_l2.output(0)], 3.2) )
        pipe23 = self.add_block( Pipe('pipe23', [dummy_l2.output(0), dummy_l3.output(0)], 3.3) )
        pipe30 = self.add_block( Pipe('pipe30', [dummy_l3.output(0), zero_l.output(0)], None, [[0, 4.6/60, 10.1/60, 16.6/60, 1], [1.975, 1.92, 1.85, 1.82, 1.62]]) )

        # tanks
        no_flow = self.add_block( Const('no_flow', 0) )
        rect1 = self.add_block( Generator('rect1', _tp, 'square', 0.5, 0.5, 300, 180, 0.5) )
        rect2 = self.add_block( Generator('rect2', _tp, 'square', 0.5, -0.5, 300, 90, 0.5) )
        rect = self.add_block( SumDiff('rect', [1, 1]) )
        rect.add_input(rect1.output(0))
        rect.add_input(rect2.output(0))
        dist_enable = self.add_block( Const('dist_enable', 0) )
        dist_random = self.add_block( MulDiv('dist_random', [1, 1]) )
        dist_random.add_input(rect.output(0))
        dist_random.add_input(dist_enable.output(0))
        dist_const = self.add_block( Const('dist_const', 7) )
        dist_lmin = self.add_block( SumDiff('dist_lmin', [1, 1]) )
        dist_lmin.add_input(dist_const.output(0))
        dist_lmin.add_input(dist_random.output(0))
        dist = self.add_block( Gain('dist', 1.0/60000))
        dist.add_input(dist_lmin.output(0))
        tank1 = self.add_block(Tank('tank1', [self.input(0), no_flow.output(0), pipe12.output(0)], _tp, 0.38, [0, 1], _init[0]))
        tank2 = self.add_block(Tank('tank2', [no_flow.output(0), pipe12.output(0), pipe23.output(0)], _tp, 1.2, [0, 1], _init[1]))
        tank3 = self.add_block(Tank('tank3', [dist.output(0), pipe23.output(0), pipe30.output(0)], _tp, 1.2, [0, 1], _init[2]))

        # feedback
        dummy_l1.add_input(tank1.output(0))
        dummy_l2.add_input(tank2.output(0))
        dummy_l3.add_input(tank3.output(0))

        # Add outputs
        self.add_output(tank1.output(0))
        self.add_output(tank2.output(0))
        self.add_output(tank3.output(0))
        self.add_output(pipe30.output(0))
        self.add_output(dist_lmin.output(0))

class PumpPipe(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): F [m3/h]
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        flow_scale = self.add_block( Gain('flow_scale', 10000) )
        flow_scale.add_input(self.input(0))
        pressure_100 = self.add_block( Equation('pressure_100', [507.29, -24.754, -10.786]) )
        pressure_100.add_input(flow_scale.output(0))
        pump_ctrl = self.add_block( Const('pump_ctrl', 100) )
        ctrl_100_weight = self.add_block( LookupTable1D('ctrl_100_weight', 'linear', [0, 80, 100], [0, 0, 1]) )
        ctrl_100_weight.add_input(pump_ctrl.output(0))
        pressure_100_raw = self.add_block( MulDiv('pressure_100_raw', [1, 1]) )
        pressure_100_raw.add_input(pressure_100.output(0))
        pressure_100_raw.add_input(ctrl_100_weight.output(0))
        pressure = self.add_block( Gain('pressure', 0.5) )
        pressure.add_input(pressure_100_raw.output(0))

        # Add outputs: P [kPa]
        self.add_output(pressure.output(0))

class Positioner(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): CV [%]
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        scale = self.add_block( Gain('scale', 0.01) )
        scale.add_input(self.input(0))
        foi = self.add_block( FirstOrderInertia('foi', _tp, 1, 0.1) )
        foi.add_input(scale.output(0))

        # Add outputs: G [0-1]
        self.add_output(foi.output(0))

class Valve(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): G [0-1], P1 [kPa], P2 [kPa]
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        #   dP
        dp = self.add_block( SumDiff('dp', [1, -1]) )
        dp.add_input(self.input(1))
        dp.add_input(self.input(2))
        dpabs = self.add_block( Abs('dpabs') )
        dpabs.add_input(dp.output(0))
        dpsign = self.add_block( Sign('dpsign') )
        dpsign.add_input(dp.output(0))

        #   Params
        kv_max = self.add_block( Const('kv_max', 0.00049) )
        alfa = self.add_block( Const('alfa', 2) )
        ro = self.add_block( Const('ro', 1) )
        lin_range = self.add_block( Const('lin_range', 0.1) )

        #   G
        g_scale = self.add_block( Limiter('g_scale', [0, 1]) )
        g_scale.add_input(self.input(0))
        g_linrange = self.add_block( SumDiff('g_linrange', [1, -1]) )
        g_linrange.add_input(g_scale.output(0))
        g_linrange.add_input(lin_range.output(0))

        #   constant%
        c1_1 = self.add_block( Const('c1_1', 1) )
        m1_1 = self.add_block( SumDiff('m1_1', [1, -1]) )
        m1_1.add_input(g_scale.output(0))
        m1_1.add_input(c1_1.output(0))
        m1_11 = self.add_block( MulDiv('m1_11', [1, 1]) )
        m1_11.add_input(m1_1.output(0))
        m1_11.add_input(alfa.output(0))
        char1 = self.add_block( Exp('char') )
        char1.add_input(m1_11.output(0))
        m1_2 = self.add_block( MulDiv('m1_2', [1, -1]) )
        m1_2.add_input(dpabs.output(0))
        m1_2.add_input(ro.output(0))
        m1_21 = self.add_block( Pow('m1_21', 0.5) )
        m1_21.add_input(m1_2.output(0))
        m1_211 = self.add_block( Gain('m1_211', 0.1) )
        m1_211.add_input(m1_21.output(0))
        fconstpercent = self.add_block( MulDiv('fconstpercent', [1, 1, 1]) )
        fconstpercent.add_input(char1.output(0))
        fconstpercent.add_input(kv_max.output(0))
        fconstpercent.add_input(m1_211.output(0))

        #   linear
        c2_1 = self.add_block( Const('c2_1', 1) )
        m2_1 = self.add_block( SumDiff('m2_1', [1, -1]) )
        m2_1.add_input(lin_range.output(0))
        m2_1.add_input(c2_1.output(0))
        m2_11 = self.add_block( MulDiv('m2_11', [1, 1]) )
        m2_11.add_input(m2_1.output(0))
        m2_11.add_input(alfa.output(0))
        char2 = self.add_block( Exp('char2') )
        char2.add_input(m2_11.output(0))
        m2_2 = self.add_block( MulDiv('m2_2', [1, -1]) )
        m2_2.add_input(dpabs.output(0))
        m2_2.add_input(ro.output(0))
        m2_21 = self.add_block( Pow('m2_21', 0.5) )
        m2_21.add_input(m2_2.output(0))
        m2_211 = self.add_block( Gain('m2_211', 0.1) )
        m2_211.add_input(m2_21.output(0))
        flinear = self.add_block( MulDiv('flinear', [1, 1, -1, 1, 1]) )
        flinear.add_input(char2.output(0))
        flinear.add_input(kv_max.output(0))
        flinear.add_input(lin_range.output(0))
        flinear.add_input(g_scale.output(0))
        flinear.add_input(m2_211.output(0))

        #   F
        switch = self.add_block( Switch('switch', 0) )
        switch.add_input(flinear.output(0))
        switch.add_input(g_linrange.output(0))
        switch.add_input(fconstpercent.output(0))
        fsum = self.add_block( MulDiv('fsum', [1, 1]) )
        fsum.add_input(switch.output(0))
        fsum.add_input(dpsign.output(0))
        f = self.add_block( FirstOrderInertia('f', _tp, 1, 1) )
        f.add_input(fsum.output(0))

        # Add outputs: dp [kPa], F [m3/h]
        self.add_output(dp.output(0))
        self.add_output(f.output(0))

class ControlValve(Subsystem):
    # @param _name unique (in parent object) block name
    # @param _inputs required inputs ([Value, ...]): CV [%], P1 [kPa], P2 [kPa]
    # @param _tp sampling time
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        positioner = self.add_block( Positioner('positioner', [self.input(0)], _tp) )
        valve = self.add_block( Valve('valve', [positioner.output(0), self.input(1), self.input(2)], _tp) )
        position = self.add_block( Gain('position', 100) )
        position.add_input(positioner.output(0))

        # Add outputs: X [%], F [m3/h], dp [kPa]
        self.add_output(position.output(0))
        self.add_output(valve.output(1))
        self.add_output(valve.output(0))

"""
    Implementation of classical PID controller.
"""
class PID(Subsystem):
    """
        Konstruktor
        Należy dodać wejścia: SP [m], PV [m]

        @param _tp Czas próbkowania z jakim będzie działać regulator
    """
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        # Define processing structure in the form of interconnected subblocks
        # - add function block
        sp_filt = self.add_block( FirstOrderInertia('sp_filt', _tp, 1, 0.1) )
        # - add block input and connect to subsystem input
        sp_filt.add_input(self.input(0))
        pv_filt = self.add_block( FirstOrderInertia('pv_filt', _tp, 1, 2) )
        pv_filt.add_input(self.input(1))
        e = self.add_block( SumDiff('e', [1, -1]) )
        e.add_input(sp_filt.output(0))
        e.add_input(pv_filt.output(0))

        dummy_cv_lim = self.add_block( Gain('dummy_cv_lim', 1) )
        cvsat_not = self.add_block( BasicLogic('cvsat_not', 'not') )
        cvsat_not.add_input(dummy_cv_lim.output(0))
        e_antywindup = self.add_block( MulDiv('e_antywindup', [1, 1]) )
        e_antywindup.add_input(e.output(0))
        e_antywindup.add_input(cvsat_not.output(0))
        e_integ = self.add_block( FirstOrderIntegrator('e_integ', _tp, 1, 1) )
        e_integ.add_input(e_antywindup.output(0))
        ti = self.add_block( Const('ti', 15) )
        i_enable = self.add_block( Const('i_enable', 1) )
        ei = self.add_block( MulDiv('ei', [1, -1, 1]) )
        ei.add_input(e_integ.output(0))
        ei.add_input(ti.output(0))
        ei.add_input(i_enable.output(0))

        dedt = self.add_block( RealDifferentiator('dedet', _tp, 1, 1) )
        dedt.add_input(e.output(0))
        td = self.add_block( Const('td', 5) )
        d_enable = self.add_block( Const('d_enable', 1) )
        ed = self.add_block( MulDiv('ed', [1, 1, 1]) )
        ed.add_input(dedt.output(0))
        ed.add_input(td.output(0))
        ed.add_input(d_enable.output(0))

        ep_ei_ed = self.add_block( SumDiff('ep_ei_ed', [1, 1, 1]) )
        ep_ei_ed.add_input(e.output(0))
        ep_ei_ed.add_input(ei.output(0))
        ep_ei_ed.add_input(ed.output(0))

        kp = self.add_block( Const('kp', 1800) )
        scale_kp = self.add_block( Const('scale_kp', 100) )
        cv_kp = self.add_block( MulDiv('cv_kp', [1, 1, 1]) )
        cv_kp.add_input(ep_ei_ed.output(0))
        cv_kp.add_input(kp.output(0))
        cv_kp.add_input(scale_kp.output(0))
        bias = self.add_block( Const('bias', 65) )
        cv_bias = self.add_block( SumDiff('cv_bias', [1, 1]) )
        cv_bias.add_input(cv_kp.output(0))
        cv_bias.add_input(bias.output(0))
        cv_lim = self.add_block( Limiter('cv_lim', [0, 100]) )
        cv_lim.add_input(cv_bias.output(0))
        mode = self.add_block( Const('mode', 0) )
        cv_raw = self.add_block( Switch('cv_raw', 0.5) )
        cv_raw.add_input(cv_lim.output(0))
        cv_raw.add_input(mode.output(0))
        cv_raw.add_input(self.input(2))
        cv = self.add_block( FirstOrderInertia('cv', _tp, 1, 0.5) )
        cv.add_input(cv_raw.output(0))

        dummy_cv_lim.add_input(cv_lim.output(1))

        # Define subsystem outputs (add and connect to block output): CV [%], e
        self.add_output(cv.output(0))
        self.add_output(e.output(0))

from libraries.fuzzy import *

class FuzzyControl(Subsystem):
    """
        Konstruktor
        Należy dodać wejścia: SP [m], PV [m]

        @param _tp Czas próbkowania z jakim będzie działać regulator
    """
    def __init__(self, _name, _inputs, _tp):
        super().__init__(_name, _inputs)

        # Obliczenie e=SP-PV oraz de/dt
        e = self.add_block( SumDiff('e', [1, -1]) )
        e.add_input(self.input(0))
        e.add_input(self.input(1))

        de = self.add_block( RealDifferentiator('de', _tp, 1, 5) )
        de.add_input(e.output(0))

        # Bloki do przechowywania parametrów
        ke = self.add_block( Const('ke', 1) )
        kde = self.add_block( Const('kde', 0.01) )
        kdcv = self.add_block( Const('kdCV', 1) )

        # Blok regulatora fuzzy
        fcontroller = self.add_block( SimpleFuzzyController('fcontroller') )
        fcontroller.add_input(ke.output(0))
        fcontroller.add_input(kde.output(0))
        fcontroller.add_input(kdcv.output(0))
        fcontroller.add_input(e.output(0))
        fcontroller.add_input(de.output(0))

        # Całkowanie sygnału dCV
        cv = self.add_block( FirstOrderIntegrator('cv', _tp, 1, 1, [0, 100]) )
        cv.add_input(fcontroller.output(0))

        # Dodanie wyjść: CV [%], e [m]
        self.add_output(cv.output(0))
        self.add_output(e.output(0))
        self.add_output(de.output(0))