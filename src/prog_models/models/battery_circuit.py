# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from .. import prognostics_model

from math import exp, inf


class BatteryCircuit(prognostics_model.PrognosticsModel):
    """
    Prognostics model for a battery, represented by an electric circuit
    
    This class implements an equivilant circuit model as described in the following paper:
    `M. Daigle and S. Sankararaman, "Advanced Methods for Determining Prediction Uncertainty in Model-Based Prognostics with Application to Planetary Rovers," Annual Conference of the Prognostics and Health Management Society 2013, pp. 262-274, New Orleans, LA, October 2013. https://papers.phmsociety.org/index.php/phmconf/article/view/2253`
    
    Events: (1)
        EOD: End of Discharge
    
    Inputs/Loading: (1)
        i: Current draw on the battery

    States: (4)
        | tb : Battery Temperature (°C)
        | qb : Charge stored in Capacitor Cb of the equivalent circuit model
        | qcp : Charge stored in Capacitor Ccp of the equivalent circuit model
        | qcs : Charge stored in Capacitor Ccs of the equivalent circuit model

    Outputs: (2)
        | t: Temperature of battery (°C)
        | v: Voltage supplied by battery

    Model Configuration Parameters:
        | process_noise : Process noise (applied at dx/next_state). 
                    Can be number (e.g., .2) applied to every state, a dictionary of values for each 
                    state (e.g., {'x1': 0.2, 'x2': 0.3}), or a function (x) -> x
        | process_noise_dist : Optional, distribution for process noise (e.g., normal, uniform, triangular)
        | measurement_noise : Measurement noise (applied in output eqn)
                    Can be number (e.g., .2) applied to every output, a dictionary of values for each 
                    output (e.g., {'z1': 0.2, 'z2': 0.3}), or a function (z) -> z
        | measurement_noise_dist : Optional, distribution for measurement noise (e.g., normal, uniform, triangular)
        | V0 : Nominal Battery Voltage
        | Rp : Battery Parasitic Resistance 
        | qMax : Maximum Charge
        | CMax : Max Capacity
        | VEOD : End of Discharge Voltage Threshold
        | Cb0 : Battery Capacity Parameter
        | Cbp0 : Battery Capacity Parameter
        | Cbp1 : Battery Capacity Parameter
        | Cbp2 : Battery Capacity Parameter
        | Cbp3 : Battery Capacity Parameter
        | Rs : R-C Pair Parameter
        | Cs : R-C Pair Parameter
        | Rcp0 : R-C Pair Parameter
        | Rcp1 : R-C Pair Parameter
        | Rcp2 : R-C Pair Parameter
        | Ccp : R-C Pair Parameter
        | Ta : Ambient Temperature
        | Jt : Temperature parameter
        | ha : Heat transfer coefficient, ambient
        | hcp : Heat transfer coefficient parameter
        | hcs : Heat transfer coefficient - surface
        | x0 : Initial state
    
    Note: This is much quicker but also less accurate as the electrochemistry model
    """
    events = ['EOD']
    inputs = ['i']
    states = ['tb', 'qb', 'qcp', 'qcs']
    outputs = ['t',  'v']

    default_parameters = {  # Set to defaults
        'V0': 4.183,
        'Rp': 1e4,
        'qMax': 7856.3254,
        'CMax': 7777,
        'VEOD': 3.0,
        # Voltage above EOD after which voltage will be considered in SOC calculation
        'VDropoff': 0.1,
        # Capacitance 
        'Cb0': 1878.155726,
        'Cbp0': -230,
        'Cbp1': 1.2,
        'Cbp2': 2079.9,
        'Cbp3': 27.055726,
        # R-C Pairs
        'Rs': 0.0538926, 
        'Cs': 234.387,
        'Rcp0': 0.0697776,
        'Rcp1': 1.50528e-17,
        'Rcp2': 37.223,
        'Ccp': 14.8223,
        # Temperature Parameters
        'Ta': 18.95,
        'Jt': 800,
        'ha': 0.5,
        'hcp': 19,
        'hcs': 1,
        'x0': {
            'tb': 18.95,
            'qb': 7856.3254,
            'qcp': 0,
            'qcs': 0
        },
        # current ratings
        'nomCapacity': 2.2,  # nominal capacity, Ah
        'CRateMin': 0.7,  # current necessary for cruise,
        'CRateMax': 2.5   # current necessary for hover
        # CRateMin, CRateMax based on values determined in `C. Silva and W. Johnson, "VTOL Urban Air Mobility Concept Vehicles for Technology Development" Aviation and Aeronautics Forum (Aviation 2018),June 2018. https://arc.aiaa.org/doi/abs/10.2514/6.2018-3847`
    }

    state_limits = {
        'tb': (-273.15, inf),  # Limited by absolute zero. Note thermal runaway temperature is ~130°C, so the model is not valid after that temperature.
        'qb': (0, inf)
    }

    def initialize(self, u={}, z={}):
        return self.parameters['x0']

    def dx(self, x, u):
        # Keep this here- accessing member can be expensive in python- this optimization reduces runtime by almost half!
        parameters = self.parameters
        Rs = parameters['Rs']
        Vcs = x['qcs']/parameters['Cs']
        Vcp = x['qcp']/parameters['Ccp']
        SOC = (parameters['CMax'] - parameters['qMax'] +
               x['qb'])/parameters['CMax']
        Cb = parameters['Cbp0']*SOC**3 + parameters['Cbp1'] * \
            SOC**2 + parameters['Cbp2']*SOC + parameters['Cbp3']
        Rcp = parameters['Rcp0'] + parameters['Rcp1'] * \
            exp(parameters['Rcp2']*(-SOC + 1))
        Vb = x['qb']/Cb
        Tbdot = (Rcp*Rs*parameters['ha']*(parameters['Ta'] - x['tb']) + Rcp*Vcs**2*parameters['hcs'] + Rs*Vcp**2*parameters['hcp']) \
            / (parameters['Jt']*Rcp*Rs)
        Vp = Vb - Vcp - Vcs
        ip = Vp/parameters['Rp']
        ib = u['i'] + ip
        icp = ib - Vcp/Rcp
        ics = ib - Vcs/Rs

        return {
            'tb': Tbdot,
            'qb': -ib,
            'qcp': icp,
            'qcs': ics
        }
    
    def event_state(self, x):
        parameters = self.parameters
        z = self.output(x)
        charge_EOD = (parameters['CMax'] -
                      parameters['qMax'] + x['qb'])/parameters['CMax']
        voltage_EOD = (z['v'] - self.parameters['VEOD']) / \
            self.parameters['VDropoff']
        return {
            'EOD': min(charge_EOD, voltage_EOD)
        }

    def output(self, x):
        parameters = self.parameters
        Vcs = x['qcs']/parameters['Cs']
        Vcp = x['qcp']/parameters['Ccp']
        SOC = (parameters['CMax'] - parameters['qMax'] + x['qb'])/parameters['CMax']
        Cb = parameters['Cbp0']*SOC**3 + parameters['Cbp1']*SOC**2 + parameters['Cbp2']*SOC + parameters['Cbp3']
        Vb = x['qb']/Cb

        return {
            't': x['tb'],
            'v': Vb - Vcp - Vcs
        }

    def threshold_met(self, x):
        parameters = self.parameters
        Vcs = x['qcs']/parameters['Cs']
        Vcp = x['qcp']/parameters['Ccp']
        SOC = (parameters['CMax'] - parameters['qMax'] + x['qb'])/parameters['CMax']
        Cb = parameters['Cbp0']*SOC**3 + parameters['Cbp1']*SOC**2 + parameters['Cbp2']*SOC + parameters['Cbp3']
        Vb = x['qb']/Cb
        V = Vb - Vcp - Vcs

        # Return true if voltage is less than the voltage threshold
        return {
             'EOD': V < parameters['VEOD']
        }
