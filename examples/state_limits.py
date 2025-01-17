# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

"""
Example demonstrating ways to use state limits. Run using the command `python -m examples.state_limits`
"""

from .new_model import ThrownObject
from math import inf

def run_example():
    # Demo model
    # Step 1: Create instance of model
    m = ThrownObject()

    # Step 2: Setup for simulation 
    def future_load(t, x=None):
        return {}

    # add state limits
    m.state_limits = {
        # object may not go below ground height
        'x': (0, inf),

        # object may not exceed the speed of light
        'v': (-299792458, 299792458)
    }

    # Step 3: Simulate to impact
    event = 'impact'
    (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(future_load, {'x':m.parameters['thrower_height']}, threshold_keys=[event], dt=0.005, save_freq=1)
    
    # Print states
    print('Example 1')
    for i, state in enumerate(states):
        print('State ', i, ': ', state)
    print()

    # Let's try setting x to a number outside of its bounds
    x0 = m.initialize(u = {}, z = {})
    x0['x'] = -1

    (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(future_load, {'x':m.parameters['thrower_height']}, threshold_keys=[event], dt=0.005, save_freq=1, x = x0)

    # Print states
    print('Example 2')
    for i, state in enumerate(states):
        print('State ', i, ': ', state)
    print()

    # Let's see what happens when the objects speed aproaches its limit
    x0 = m.initialize(u = {}, z = {})
    x0['x'] = 1000000000
    x0['v'] = 0
    m.parameters['g'] = -50000000
    
    print('Example 3')
    (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(future_load, {'x':m.parameters['thrower_height']}, threshold_keys=[event], dt=0.005, save_freq=0.3, x = x0, print = True)

# This allows the module to be executed directly 
if __name__=='__main__':
    run_example()