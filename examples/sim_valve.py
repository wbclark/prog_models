# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

"""
Example of a pneumatic valve being simulated until threshold is met. Run using the command `python -m examples.sim_valve`
"""

from prog_models.models.pneumatic_valve import PneumaticValve

def run_example(): 
    # Create a model object
    valv = PneumaticValve(process_noise= 0)

    # Define future loading function
    cycle_time = 20
    def future_loading(t, x=None):
            t = t % cycle_time
            if t < cycle_time/2:
                return {
                    'pL': 3.5e5,
                    'pR': 2.0e5,
                    # Open Valve
                    'uTop': False,
                    'uBot': True
                }
            else:
                return {
                    'pL': 3.5e5,
                    'pR': 2.0e5,
                    # Close Valve
                    'uTop': True,
                    'uBot': False
                }

    # Simulate to threshold
    print('\n\n------------------------------------------------')
    print('Simulating to threshold\n\n')
    # Configure options
    config = {'dt': 0.01, 'horizon': 800, 'save_freq': 60}
    # Set wear parameter for spring to 1
    valv.parameters['x0']['wk'] = 1

    # Define first measured output. This is needed by the simulat_to_threshold method to initialize state
    first_output = valv.output(valv.initialize(future_loading(0)))
    # Simulate
    (times, inputs, states, outputs, event_states) = valv.simulate_to_threshold(future_loading, first_output, **config)

    # Print Results
    for i in range(len(times)):
        print("Time: {}\n\tInput: {}\n\tState: {}\n\tOutput: {}\n\tEvent State: {}\n".format(times[i], inputs[i], states[i], outputs[i], event_states[i]))

    # Simulate to threshold again but with a different wear mode
    print('\n\n------------------------------------------------')
    print('Simulating to threshold\n\n')
    # Configure options
    config = {'dt': 0.01, 'horizon': 800, 'save_freq': 60}
    # Reset wear parameter for spring to 0, set wear parameter for friction to 1
    valv.parameters['x0']['wk'] = 0
    valv.parameters['x0']['wr'] = 1

    # Define first measured output. This is needed by the simulat_to_threshold method to initialize state
    first_output = valv.output(valv.initialize(future_loading(0)))
    # Simulate
    (times, inputs, states, outputs, event_states) = valv.simulate_to_threshold(future_loading, first_output, **config)

    # Print Results
    for i in range(len(times)):
        print("Time: {}\n\tInput: {}\n\tState: {}\n\tOutput: {}\n\tEvent State: {}\n".format(times[i], inputs[i], states[i], outputs[i], event_states[i]))
    print()

# This allows the module to be executed directly
if __name__ == '__main__':
    run_example()