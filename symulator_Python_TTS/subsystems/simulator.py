from common.utils import progress_bar
from common.path import Path
from common.with_io_vars import WithIOVars
from subsystems.templates import *
from libraries.modelling import KerasModelFirstOrder

"""
    Reprezentacja symulatora
"""
class TtsPidSim(WithIOVars):
    """
        Konstruktor

        @param _tp Okres próbkowania. Wykorzystywany do obliczania zaleśnoci dynamicznych
        @param _pr Słownik krotności przetwarzania dla części sterowania i monitorowania
    """
    def __init__(self, _tp, _pr, _use_fuzzy_control=False, _use_L3_modelling=None):
        super().__init__()
        self.tp = _tp
        self.paths = {}
        self.pr = _pr
        self.k = 0

        # SP generator
        generator = Path('generator', self.pr['monit'])
        self.paths['generator'] = generator

        time = generator.add_block( Time('time', self.tp*self.pr['monit']) )
        hole_range = generator.add_block( LookupTable1D('hole_range', 'last',
            [0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700, 3000, 3300, 3600, 3900, 4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 6900, 7200, 7500, 7800, 8100, 8400, 8700, 9000, 9300, 9600, 9900, 10200, 10500, 10800, 11100, 11400, 11700, 12000, 12300, 12600, 12900, 13200, 13500, 13800, 14100, 14400, 14700, 15000],
           [0, 0.65, 0.14, 0.22, 0.08, 0.35, 0.45, 0.6, 0.41, 0.5, 0.75, 0.2, 0.47, 0.25, 0.7, 0.93, 0.34, 0.8, 0.53, 0.7, 0.28, 0.61, 0.22, 0.68, 0.83, 0.5, 0.9, 0.29, 0.12, 0.45, 0.2, 0.86, 0.7, 0.04, 0.48, 0.28, 0.83, 0.5, 0.39, 0.83, 0.6, 0.87, 0.67, 0.36, 0.3, 0.93, 0.33, 0.71, 0.31, 0.15, 0], True) )
        hole_range.add_input(time.output(0))
        sp_t_range = generator.add_block( Gain('sp_t_range', 0.41) )
        sp_t_range.add_input(hole_range.output(0))
        sp_t_wp = generator.add_block( LookupTable1D('sp_t_wp', 'last',
            [0, 300, 600, 900, 1200, 1500, 1800, 2100, 2400, 2700],
           [0.2, 0.25, 0.2, 0.15, 0.2, 0.225, 0.2, 0.175, 0.2, 0.2], True) )
        sp_t_wp.add_input(time.output(0))
        sp_t_sin = generator.add_block( Generator('sp_t_sin', self.tp*self.pr['monit'], 'sine', 0.15, 0.2, 600, 0) )
        sp_man = generator.add_block( Const('sp_man', 0) )
        sp_sel = generator.add_block( Const('sp_sel', 0) )
        sp = generator.add_block( MultiSwitch('sp') )
        sp.add_input(sp_sel.output(0))
        sp.add_input(sp_man.output(0))
        sp.add_input(sp_t_range.output(0))
        sp.add_input(sp_t_wp.output(0))
        sp.add_input(sp_t_sin.output(0))

        cvman_t1 = generator.add_block( Generator('cvman_t1', self.tp*self.pr['monit'], 'saw tooth', 100, 0, 1000, 0) )
        cvman_t2 = generator.add_block( Generator('cvman_t2', self.tp*self.pr['monit'], 'saw tooth', -100, 100, 1000, 0) )
        cvman_t1_enable = generator.add_block( Generator('cvman_t1_enable', self.tp*self.pr['monit'], 'square', 0.5, 0.5, 2000, 0, 0.5) )
        cvman_t2_enable = generator.add_block( Generator('cvman_t2_enable', self.tp*self.pr['monit'], 'square', 0.5, 0.5, 2000, 180, 0.5) )
        cvman_triangle1 = generator.add_block( MulDiv('cvman_triangle1', [1, 1]) )
        cvman_triangle1.add_input(cvman_t1.output(0))
        cvman_triangle1.add_input(cvman_t1_enable.output(0))
        cvman_triangle2 = generator.add_block( MulDiv('cvman_triangle2', [1, 1]) )
        cvman_triangle2.add_input(cvman_t2.output(0))
        cvman_triangle2.add_input(cvman_t2_enable.output(0))
        cvman_triangle = generator.add_block( SumDiff('cvman_triangle', [1, 1]) )
        cvman_triangle.add_input(cvman_triangle1.output(0))
        cvman_triangle.add_input(cvman_triangle2.output(0))
        cvman_man = generator.add_block(Const('cvman_man', 0))
        cvman_sel = generator.add_block( Const('cvman_sel', 1) )
        cvman = generator.add_block( MultiSwitch('cvman') )
        cvman.add_input(cvman_sel.output(0))
        cvman.add_input(cvman_man.output(0))
        cvman.add_input(cvman_triangle.output(0))

        #  add ins/outs
        self.add_in_var('SPman', sp_man.const)
        self.add_in_var('SPmode', sp_sel.const)
        self.add_in_var('CVman', cvman_man.const)
        self.add_in_var('CVmode', cvman_sel.const)
        self.add_out_var('t', Value(0))
        self.add_out_var('SP', sp.output(0))

        # Controller path
        #   working with tpcont = tpsim * pr.control (default=0.2 [s])
        controller_sim = Path('controller_sim', self.pr['control'])
        self.paths['controller_sim'] = controller_sim

        #   PV measurement. Block also used to make control feedback.
        pv_noise = controller_sim.add_block( Random('pv_noise', 0, 0.0013333333333) )
        pv_measure = controller_sim.add_block( SumDiff('pv_measure', [1, 1]) )
        pv_measure.add_input(pv_noise.output(0))

        if not _use_fuzzy_control:
            # Classical PID controller
            controller = controller_sim.add_block( PID('controller', [sp.output(0), pv_measure.output(0), cvman.output(0)], self.tp*self.pr['control']) )
            #   add ins/outs: controller parameters
            self.add_in_var('kp', controller.blocks['kp'].const)
            self.add_in_var('Ti', controller.blocks['ti'].const)
            self.add_in_var('Td', controller.blocks['td'].const)
            self.add_in_var('Bias', controller.blocks['bias'].const)
            self.add_in_var('Ienable', controller.blocks['i_enable'].const)
            self.add_in_var('Denable', controller.blocks['d_enable'].const)
            self.add_in_var('PIDmode', controller.blocks['mode'].const)
        else:
            # Fuzzy controller
            controller = controller_sim.add_block( FuzzyControl('controller', [sp.output(0), pv_measure.output(0)], self.tp*self.pr['control']) )
            #   add ins/outs: controller parameters
            self.add_in_var('ke', controller.blocks['ke'].const)
            self.add_in_var('kde', controller.blocks['kde'].const)
            self.add_in_var('kdCV', controller.blocks['kdCV'].const)
            #   - monitoring variables: de
            self.add_out_var('de', controller.output(2))

        #   - monitoring variables: CV, PV, e
        self.add_out_var('CV', controller.output(0))
        self.add_out_var('PV', pv_measure.output(0))
        self.add_out_var('e', controller.output(1))

        # Simulator path
        tts_sim = Path('tts_sim')
        self.paths['tts_sim'] = tts_sim

        #  pump+pipe+control valve
        dummy_f = tts_sim.add_block( Gain('dummy_f', 1) )
        pump_pipe = tts_sim.add_block( PumpPipe('pump_pipe', [dummy_f.output(0)], self.tp) )

        p_atm = tts_sim.add_block( Const('p_atm', 1.013) )
        control_valve = tts_sim.add_block( ControlValve('control_valve', [controller.output(0), pump_pipe.output(0), p_atm.output(0)], self.tp) )
        dummy_f.add_input(control_valve.output(1))

        #  three tanks
        three_tanks = tts_sim.add_block( ThreeTanks('three_tanks', [control_valve.output(1)], self.tp, [0.018, 0.018, 0.018]) )

        # Process-Controller feadback: use L3 measurement
        if _use_L3_modelling!='control':
            pv_measure.add_input(three_tanks.output(2))

        # Measurements path
        monit_sim = Path('monit_sim', self.pr['monit'])
        self.paths['monit_sim'] = monit_sim

        #  scaling and noise
        f1 = monit_sim.add_block( Gain('f1', 60000) )
        f1.add_input(control_valve.output(1))

        f2 = monit_sim.add_block( Gain('f2', 60000) )
        f2.add_input(three_tanks.output(3))

        p_noise = monit_sim.add_block( Random('p_noise', 0, 0.3) )
        p_dist = monit_sim.add_block( SumDiff('p_dist', [1, 1]) )
        p_dist.add_input(p_noise.output(0))
        p_dist.add_input(pump_pipe.output(0))
        g_noise = monit_sim.add_block( Random('g_noise', 0, 0.15) )
        g_dist = monit_sim.add_block( SumDiff('g_dist', [1, 1]) )
        g_dist.add_input(g_noise.output(0))
        g_dist.add_input(control_valve.output(0))
        dp_noise = monit_sim.add_block( Random('dp_noise', 0, 0.3) )
        dp_dist = monit_sim.add_block( SumDiff('dp_dist', [1, 1]) )
        dp_dist.add_input(dp_noise.output(0))
        dp_dist.add_input(control_valve.output(2))
        f1_noise = monit_sim.add_block( Random('f1_noise', 0, 0.083) )
        f1_dist = monit_sim.add_block( SumDiff('f1_dist', [1, 1]) )
        f1_dist.add_input(f1_noise.output(0))
        f1_dist.add_input(f1.output(0))
        l1_noise = monit_sim.add_block( Random('l1_noise', 0, 0.001666666) )
        l1_dist = monit_sim.add_block( SumDiff('l1_dist', [1, 1]) )
        l1_dist.add_input(l1_noise.output(0))
        l1_dist.add_input(three_tanks.output(0))
        l2_noise = monit_sim.add_block( Random('l2_noise', 0, 0.0003333333333) )
        l2_dist = monit_sim.add_block( SumDiff('l2_dist', [1, 1]) )
        l2_dist.add_input(l2_noise.output(0))
        l2_dist.add_input(three_tanks.output(1))
        l3_dist = monit_sim.add_block( Gain('l3_dist', 1) )
        l3_dist.add_input(pv_measure.output(0))
        f2_noise = monit_sim.add_block( Random('f2_noise', 0, 0.083) )
        f2_dist = monit_sim.add_block( SumDiff('f2_dist', [1, 1]) )
        f2_dist.add_input(f2_noise.output(0))
        f2_dist.add_input(f2.output(0))

        # Soft-sensor: modelling L3
        if _use_L3_modelling=='monit' or _use_L3_modelling=='control' :
            l3_pred = monit_sim.add_block( KerasModelFirstOrder('l3_pred', 'L3_L2_1_L3_1', 'mro'))
            l3_pred.add_input(l2_dist.output(0))
            l3_pred.add_input(l3_dist.output(0))

        # Process-Controller feadback: use L3 model output
        if _use_L3_modelling=='control':
            pv_measure.add_input(l3_pred.output(0))

        #  add ins/outs
        self.add_in_var('distEnable', three_tanks.blocks['dist_enable'].const)
        self.add_out_var('P', p_dist.output(0))
        self.add_out_var('G', g_dist.output(0))
        self.add_out_var('dP', dp_dist.output(0))
        self.add_out_var('F1', f1_dist.output(0))
        self.add_out_var('L1', l1_dist.output(0))
        self.add_out_var('L2', l2_dist.output(0))
        self.add_out_var('L3', l3_dist.output(0))
        self.add_out_var('F2', f2_dist.output(0))
        self.add_out_var('dist', three_tanks.output(4))

        if _use_L3_modelling=='monit' or _use_L3_modelling=='control' :
            self.add_out_var('L3_pred', l3_pred.output(0))

    """
        Wykonanie kroku symulacji

        @param _log_output Czy logowaść wyjścia? Domyślnie: True
        
        @return Lista wartości zmiennych wyjściowych
    """
    def simulation_step(self, _log_output=True):
        for path in self.paths.values():
            path.simulation_step()
        self.out_var('t').set(self.k * self.tp)

        rval = None
        if _log_output:
            rval = []
            for k, v in self.out_vars.items():
              rval.append(v.get())

        self.k += 1
        return rval

    """
        Ścieżka przetwarzania

        @param _name Nazwa ścieżki
        
        @return Obiekt ścieżki Path
    """
    def path(self, _name):
        return self.paths[_name]

    """
        Inicjalizacja - ustawienie wartości początkowych/domyślnych
    """
    def init_sim(self):
        self.k = 0
        for path in self.paths.values():
            path.init_sim()

    """
        Wykonanie symulacji w trybie wsadowym

        @param _tsim Okres symulacji
        @param _log_output_mode Zapis danych z określonym okresem próbkowania {'monit', 'control'}. Domyślnie: None
        @param _progress Czy wyświetlić wskaźnik postępu? Domyślnie: False
        
        @return Słownik wektorów wartości zmiennych wyjściowych
    """
    def simulate(self, _tsim, _log_output_mode=None, _progress=False):
        rval = {}
        for ovk in self.out_vars.keys():
            rval[ovk] = []

        steps_end = _tsim/self.tp

        self.init_sim()
        while self.k < steps_end:
            vars = self.simulation_step(_log_output_mode is not None)

            if _log_output_mode:
                if (self.k-1) % self.pr[_log_output_mode]  == 0:
                    for i, k in enumerate(self.out_vars.keys()):
                        rval[k].append(vars[i])

            progress_bar(int(self.k * self.tp), _tsim)

        return rval

    """
        Pobranie wartości wyjść

        @return Lista wartości zmiennych wyjściowych
    """
    def get_outputs(self):
        rval = {'t': self.t}
        for k, v in self.out_vars.items():
            rval[k] = v.get()
        return rval