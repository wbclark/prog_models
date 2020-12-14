# Copyright © 2020 United States Government as represented by the Administrator of the National Aeronautics and Space Administration.  All Rights Reserved.
import unittest
from prog_models import *
from prog_models.models import *
from copy import deepcopy

class MockModel():
    states = ['a', 'b', 'c']
    inputs = ['i1', 'i2']
    outputs = ['o1']
    default_parameters = {
        'p1': 1.2,
        'x0': {'a': 1, 'b': [3, 2], 'c': -3.2}
    }

    def initialize(self, u, z):
        return deepcopy(self.parameters['x0'])

    def next_state(self, t, x, u, dt):
        x['a']+= u['i1']*dt
        x['c']-= u['i2']
        return x

    def output(self, t, x):
        return {'o1': x['a'] + sum(x['b']) + x['c']}

class MockProgModel(MockModel, prognostics_model.PrognosticsModel):
    events = ['e1', 'e2']

    def event_state(self, t, x):
        return {
            'e1': max(1-t/5.0,0),
            'e2': max(1-t/15.0,0)
            }

    def threshold_met(self, t, x):
        return {
            'e1': self.event_state(t, x)['e1'] < 1e-6, 
            'e2': self.event_state(t, x)['e2'] < 1e-6, 
            }

class TestModels(unittest.TestCase):
    def test_templates(self):
        import prog_model_template
        m = prog_model_template.ProgModelTemplate()
        # TODO(CT): More

    def test_broken_models(self):
        class missing_states(prognostics_model.PrognosticsModel):
            inputs = ['i1', 'i2']
            outputs = ['o1']
            parameters = {'process_noise':0.1}
            def initialize(self, u, z):
                pass
            def next_state(self, t, x, u, dt):
                pass
            def output(self, t, x):
                pass
        class empty_states(prognostics_model.PrognosticsModel):
            states = []
            inputs = ['i1', 'i2']
            outputs = ['o1']
            parameters = {'process_noise':0.1}
            def initialize(self, u, z):
                pass
            def next_state(self, t, x, u, dt):
                pass
            def output(self, t, x):
                pass
        class missing_inputs(prognostics_model.PrognosticsModel):
            states = ['x1', 'x2']
            outputs = ['o1']
            parameters = {'process_noise':0.1}
            def initialize(self, u, z):
                pass
            def next_state(self, t, x, u, dt):
                pass
            def output(self, t, x):
                pass
        class missing_outputs(prognostics_model.PrognosticsModel):
            states = ['x1', 'x2']
            inputs = ['i1']
            parameters = {'process_noise':0.1}
            def initialize(self, u, z):
                pass
            def next_state(self, t, x, u, dt):
                pass
            def output(self, t, x):
                pass
        class missing_initiialize(prognostics_model.PrognosticsModel):
            inputs = ['i1']
            states = ['x1', 'x2']
            outputs = ['o1']
            parameters = {'process_noise':0.1}
            def next_state(self, t, x, u, dt):
                pass
            def output(self, t, x):
                pass
        # This one is broken with merging deriv  model and prognsotics model
        # class missing_next_state(prognostics_model.PrognosticsModel):
        #     inputs = ['i1']
        #     states = ['x1', 'x2']
        #     outputs = ['o1']
        #     parameters = {'process_noise':0.1}
        #     def initialize(self, u, z):
        #         pass
        #     def output(self, t, x):
        #         pass
        class missing_output(prognostics_model.PrognosticsModel):
            inputs = ['i1']
            states = ['x1', 'x2']
            outputs = ['o1']
            parameters = {'process_noise':0.1}
            def initialize(self, u, z):
                pass
            def next_state(self, t, x, u, dt):
                pass

        try: 
            m = missing_states()
            self.fail("Should not have worked, missing 'states'")
        except ProgModelTypeError:
            pass

        try: 
            m = empty_states()
            self.fail("Should not have worked, empty 'states'")
        except ProgModelTypeError:
            pass

        try: 
            m = missing_inputs()
            self.fail("Should not have worked, missing 'inputs'")
        except ProgModelTypeError:
            pass

        try: 
            m = missing_outputs()
            self.fail("Should not have worked, missing 'outputs'")
        except ProgModelTypeError:
            pass

        try: 
            m = missing_initiialize()
            self.fail("Should not have worked, missing 'initialize' method")
        except TypeError:
            pass

        # This is broken with integration of deriv and prog model
        # try: 
        #     m = missing_next_state()
        #     self.fail("Should not have worked, missing 'next_state' method")
        # except TypeError:
        #     pass

        try: 
            m = missing_output()
            self.fail("Should not have worked, missing 'output' method")
        except TypeError:
            pass

    def test_prog_model(self):
        m = MockProgModel() # Should work- sets default
        m = MockProgModel({'process_noise': 0.0})
        x0 = m.initialize({}, {})
        self.assertEqual(x0, m.parameters['x0'])
        x = m.next_state(0, x0, {'i1': 1, 'i2': 2.1}, 0.1)
        self.assertAlmostEqual(x['a'], 1.1, 6)
        self.assertAlmostEqual(x['c'], -5.3, 6)
        self.assertEqual(x['b'], [3, 2])
        z = m.output(0, x)
        self.assertAlmostEqual(z['o1'], 0.8, 5)
        e = m.event_state(0, {})
        t = m.threshold_met(0, {})
        self.assertAlmostEqual(e['e1'], 1.0, 5)
        self.assertFalse(t['e1'])
        e = m.event_state(5, {})
        self.assertAlmostEqual(e['e1'], 0.0, 5)
        t = m.threshold_met(5, {})
        self.assertTrue(t['e1'])
        t = m.threshold_met(10, {})
        self.assertTrue(t['e1'])

    def test_model_gen(self):
        keys = {
            'states': ['a', 'b', 'c'],
            'inputs': ['i1', 'i2'],
            'outputs': ['o1'],
            'events': ['e1']
        }

        def initialize(u, z):
            return {'a': 1, 'b': 3, 'c': -3.2}

        def next_state(t, x, u, dt):
            x['a']+= u['i1']*dt
            x['c']-= u['i2']
            return x

        def dx(t, x, u):
            return {'a': u['i1'], 'b': 0, 'c': u['i2']}

        def output(t, x):
            return {'o1': x['a'] + x['b'] + x['c']}

        def event_state(t, x):
            return {'e1': max(1-t/5.0,0)}

        def threshold_met(t, x):
            return {'e1': max(1-t/5.0,0) < 1e-6}

        m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, output, next_state_eqn = next_state, event_state_eqn = event_state, threshold_eqn = threshold_met)
        x0 = m.initialize({}, {})
        x = m.next_state(0, x0, {'i1': 1, 'i2': 2.1}, 0.1)
        self.assertAlmostEqual(x['a'], 1.1, 6)
        self.assertAlmostEqual(x['c'], -5.3, 6)
        self.assertEqual(x['b'], 3)
        z = m.output(0, x)
        self.assertAlmostEqual(z['o1'], -1.2, 5)
        e = m.event_state(0, {})
        t = m.threshold_met(0, {})
        self.assertAlmostEqual(e['e1'], 1.0, 5)
        self.assertFalse(t['e1'])
        e = m.event_state(5, {})
        self.assertAlmostEqual(e['e1'], 0.0, 5)
        t = m.threshold_met(5.1, {})
        self.assertTrue(t['e1'])
        t = m.threshold_met(10, {})
        self.assertTrue(t['e1'])

        # Without event_state or threshold
        keys = {
            'states': ['a', 'b', 'c'],
            'inputs': ['i1', 'i2'],
            'outputs': ['o1']
        }
        m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, output, next_state_eqn=next_state)
        x0 = m.initialize({}, {})
        x = m.next_state(0, x0, {'i1': 1, 'i2': 2.1}, 0.1)
        self.assertAlmostEqual(x['a'], 1.1, 6)
        self.assertAlmostEqual(x['c'], -5.3, 6)
        self.assertEqual(x['b'], 3)
        z = m.output(0, x)
        self.assertAlmostEqual(z['o1'], -1.2, 5)
        e = m.event_state(5, {})
        self.assertDictEqual(e, {})
        t = m.threshold_met(5.1, {})
        self.assertDictEqual(t, {})

        # Deriv Model
        m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, output, dx_eqn=dx)
        x0 = m.initialize({}, {})
        dx = m.dx(0, x0, {'i1': 1, 'i2': 2.1})
        self.assertAlmostEqual(dx['a'], 1, 6)
        self.assertAlmostEqual(dx['b'], 0, 6)
        self.assertAlmostEqual(dx['c'], 2.1, 6)
        x = m.next_state(0, x0, {'i1': 1, 'i2': 2.1}, 0.1)
        self.assertAlmostEqual(x['a'], 1.1, 6)
        self.assertAlmostEqual(x['c'], -2.99, 6)
        self.assertEqual(x['b'], 3)

    def test_broken_model_gen(self):
        keys = {
            'states': ['a', 'b', 'c'],
            'inputs': ['i1', 'i2'],
            'outputs': ['o1'],
            'events': ['e1']
        }

        def initialize(u, z):
            return {'a': 1, 'b': [3, 2], 'c': -3.2}

        def next_state(t, x, u, dt):
            x['a']+= u['i1']*dt
            x['c']-= u['i2']
            return x

        def output(t, x):
            return {'o1': x['a'] + sum(x['b']) + x['c']}

        def event_state(t, x):
            return {'e1': max(1-t/5.0,0)}

        def threshold_met(t, x):
            print("Time: ", t)
            return {'e1': max(1-t/5.0,0) < 1e-6}

        try:
            m = prognostics_model.PrognosticsModel.generate_model(keys, 7, output, next_state_eqn=next_state)
            self.fail("Should have failed- non-callable initialize eqn")
        except ProgModelTypeError:
            pass

        try:
            m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, output, next_state_eqn=[])
            self.fail("Should have failed- non-callable next_state eqn")
        except ProgModelTypeError:
            pass
        try:
            m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, output)
            self.fail("Should have failed- missing next_state and dx eqn")
        except ProgModelTypeError:
            pass

        try:
            m = prognostics_model.PrognosticsModel.generate_model(keys, initialize, {}, next_state_eqn = next_state)
            self.fail("Should have failed- non-callable output eqn")
        except ProgModelTypeError:
            pass

        try:
            incomplete_keys = {
                'states': ['a', 'b', 'c'],
                'outputs': ['o1'],
                'events': ['e1']
            }
            m = prognostics_model.PrognosticsModel.generate_model(incomplete_keys, initialize, {}, next_state_eqn = next_state)
            self.fail("Should have failed- missing inputs keys")
        except ProgModelTypeError:
            pass

        try:
            incomplete_keys = {
                'inputs': ['a'],
                'outputs': ['o1'],
                'events': ['e1']
            }
            m = prognostics_model.PrognosticsModel.generate_model(incomplete_keys, initialize, {}, next_state_eqn = next_state)
            self.fail("Should have failed- missing states keys")
        except ProgModelTypeError:
            pass

        try:
            incomplete_keys = {
                'inputs': ['a'],
                'states': ['a', 'b', 'c'],
                'events': ['e1']
            }
            m = prognostics_model.PrognosticsModel.generate_model(incomplete_keys, initialize, {}, next_state_eqn = next_state)
            self.fail("Should have failed- missing outputs keys")
        except ProgModelTypeError:
            pass

        try:
            extra_keys = {
                'inputs': ['a'],
                'states': ['a', 'b', 'c'],
                'outputs': ['o1'],
                'events': ['e1'],
                'abc': 'def'
            }
            m = prognostics_model.PrognosticsModel.generate_model(extra_keys, initialize, output, next_state_eqn = next_state)
        except ProgModelTypeError:
            self.fail("Should not have failed- extra keys")

        try:
            incomplete_keys = {
                'inputs': ['a'],
                'states': ['a', 'b', 'c'],
                'outputs': ['o1'],
                'events': ['e1']
            }
            m = prognostics_model.PrognosticsModel.generate_model(incomplete_keys, initialize, output, event_state_eqn=-3, next_state_eqn = next_state)
            self.fail("Should have failed- not callable event_state eqn")
        except ProgModelTypeError:
            pass

        try:
            incomplete_keys = {
                'inputs': ['a'],
                'states': ['a', 'b', 'c'],
                'outputs': ['o1'],
                'events': ['e1']
            }
            m = prognostics_model.PrognosticsModel.generate_model(incomplete_keys, initialize, output, event_state_eqn=event_state, threshold_eqn=-3, next_state_eqn = next_state)
            self.fail("Should have failed- not callable threshold eqn")
        except ProgModelTypeError:
            pass

    def test_sim_to_thresh(self):
        m = MockProgModel({'process_noise': 0.0})
        def load(t):
            return {'i1': 1, 'i2': 2.1}

        (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0})
        self.assertAlmostEqual(times[-1], 5.0, 5)

        (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0}, threshold_keys=['e1', 'e2'])
        self.assertAlmostEqual(times[-1], 5.0, 5)

        (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0}, threshold_keys=['e2'])
        self.assertAlmostEqual(times[-1], 15.0, 5)

        try:
            (times, inputs, states, outputs, event_states) = m.simulate_to_threshold(load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0}, threshold_keys=['e1', 'e2', 'e3'])
            self.fail("Should fail- extra threshold key")
        except ProgModelInputException:
            pass

    def test_sim_past_thresh(self):
        m = MockProgModel({'process_noise': 0.0})
        def load(t):
            return {'i1': 1, 'i2': 2.1}

        (times, inputs, states, outputs, event_states) = m.simulate_to(6, load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0})
        self.assertAlmostEqual(times[-1], 6.0, 5)
        
    def test_sim_prog(self):
        m = MockProgModel({'process_noise': 0.0})
        def load(t):
            return {'i1': 1, 'i2': 2.1}
        
        ## Check inputs
        try:
            m.simulate_to(0, load, {'o1': 0.8})
            self.fail("Should have failed- time must be greater than 0")
        except ProgModelInputException:
            pass

        try:
            m.simulate_to(-30, load, {'o1': 0.8})
            self.fail("Should have failed- time must be greater than 0")
        except ProgModelInputException:
            pass

        try:
            m.simulate_to([12], load, {'o1': 0.8})
            self.fail("Should have failed- time must be a number")
        except ProgModelInputException:
            pass

        try:
            m.simulate_to([12], load, {})
            self.fail("Should have failed- output must contain each field (e.g., o1)")
        except ProgModelInputException:
            pass

        try:
            m.simulate_to([12], 132, {})
            self.fail("Should have failed- future_load should be callable")
        except ProgModelInputException:
            pass

        ## Simulate
        (times, inputs, states, outputs, event_states) = m.simulate_to(3.5, load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0})

        # Check times
        for t in range(0, 4):
            self.assertAlmostEqual(times[t], t, 5)
        self.assertEqual(len(times), 5)
        self.assertAlmostEqual(times[-1], 3.5, 5) # Save last step (even though it's not on a savepoint)
        
        # Check inputs
        self.assertEqual(len(inputs), 5)
        for i in inputs:
            self.assertDictEqual(i, {'i1': 1, 'i2': 2.1}, "Future loading error")

        # Check states
        self.assertEqual(len(states), 5)
        a = [1, 2, 3, 4, 4.5]
        c = [-3.2, -7.4, -11.6, -15.8, -17.9]
        for (ai, ci, x) in zip(a, c, states):
            self.assertAlmostEqual(x['a'], ai, 5)
            self.assertEqual(x['b'], [3, 2])
            self.assertAlmostEqual(x['c'], ci, 5)

        # Check outputs
        self.assertEqual(len(outputs), 5)
        o = [2.8, -0.4, -3.6, -6.8, -8.4]
        for (oi, z) in zip(o, outputs):
            self.assertAlmostEqual(z['o1'], oi, 5)

        # Check event_states
        self.assertEqual(len(event_states), 5)
        e = [1.0, 0.8, 0.6, 0.4, 0.3]
        for (ei, es) in zip(e, event_states):
            self.assertAlmostEqual(es['e1'], ei, 5)

        ## Check last state saving
        (times, inputs, states, outputs, event_states) = m.simulate_to(3, load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 1.0})
        for t in range(0, 4):
            self.assertAlmostEqual(times[t], t, 5)
        self.assertEqual(len(times), 4, "Should be 4 elements in times") # Didn't save last state (because same as savepoint)

        ## Simulate
        (times, inputs, states, outputs, event_states) = m.simulate_to(3, load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 99.0, 'save_pts': [1.45, 2.45]})
        # Check times
        self.assertAlmostEqual(times[0], 0, 5)
        self.assertAlmostEqual(times[1], 1.5, 5)
        self.assertAlmostEqual(times[2], 2.5, 5)
        self.assertEqual(len(times), 4)
        self.assertAlmostEqual(times[-1], 3.0, 5) # Save last step (even though it's not on a savepoint)
        
        ## Simulate
        (times, inputs, states, outputs, event_states) = m.simulate_to(2.5, load, {'o1': 0.8}, {'dt': 0.5, 'save_freq': 99.0, 'save_pts': [1.45, 2.45]})
        # Check times
        self.assertAlmostEqual(times[0], 0, 5)
        self.assertAlmostEqual(times[1], 1.5, 5)
        self.assertAlmostEqual(times[2], 2.5, 5)
        self.assertEqual(len(times), 3)
        # Last step is a savepoint        

def run_tests():
    unittest.main()
    