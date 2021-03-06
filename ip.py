# Module level imports
from numpy import *
from fuzzy.InputVariable import InputVariable
from fuzzy.OutputVariable import OutputVariable
from fuzzy.fuzzify.Plain import Plain
from fuzzy.Adjective import Adjective

# Project level import
from control import PendulumController
from mf import flat_saw


class InvertedPendulum(object):
    """
    Dynamic model of an inverted pendulum. It calculates the linear and angular
    accelerations (represented by a and q, respectively). Speed and position
    are calculated through Euler discretization of the differential equations.
    """

    def __init__(self, l=0.5, m=0.1, mc=0.5, dt=0.01):
        """
        Initializes the pendulum.

        :Parameters:
          l
            Pendulum length (in meters)
          m
            Pendulum mass (in kilograms)
          mc
            Cart mass (in kilograms)
          dt
            Time delta for simulation (in seconds)
        """
        self.l = l
        self.m = m
        self.mc = mc
        self.dt = dt
        self.O = 0.  # Pendulum angular position in rad
        self.w = 0.  # Pendulum angular velocity in rad/s
        self.x = 0.  # Cart position in meters
        self.v = 0.  # Cart speed in meters/second

    def __pv(self, x):
        """
        Principal value of angle x (that is, -pi <= x < pi)
        """
        return (x + pi) % (2 * pi) - pi

    def set_state(self, O=0., w=0., x=0., v=0.):
        """
        Sets the state of the pendulum.

        :Parameters:
          O
            Angular position in radians (theta)
          w
            Angular velocity in radians/second (omega)
          x
            Position of the cart in meters
          v
            Speed of the cart in meters/second
        """
        self.O = self.__pv(O)
        self.w = w
        self.x = x
        self.v = v

    def get_state(self):
        """
        Get the state of the pendulum, in the form of a tuple.

        :Returns:
          A tuple containing, in order, the angular position in radians, the
          angular velocity in radians/seconds, the cart position in meters, the
          cart speed in meters/second.
        """
        return self.O, self.w, self.x, self.v

    def apply(self, F):
        """
        Given the present state of the cart, calculates the next values for the
        state variables.

        :Parameters:
          F
            Force applied to the cart
        """
        g = 9.80665  # Gravity in m/s^2
        l = self.l
        O = self.O
        w = self.w
        x = self.x
        v = self.v
        so = sin(O)
        co = cos(O)
        m = self.m
        mc = self.mc
        dt = self.dt
        M = m + mc

        q = (g * so + (-F - m * l * w * w * so) * co / M) / (l * (4. / 3. - m * co * co / M))
        a = F - (m * l * (w * w * so - q * co)) / M

        self.w = w + q * dt
        self.O = self.__pv(O + self.w * dt)
        self.v = v + a * dt
        self.x = x + self.v * dt

        return self.get_state()


def create_controller():
    controller = PendulumController()

    # Create the membership functions to variable O (inclination of the pendulum).
    # Ovbn = Very Big Negative
    # Obn  = Big Negative
    # Osn  = Small Negative
    # Oz   = Near Zero
    # Osp  = Small Positive
    # Obp  = Big Positive
    # Ovbp = Very Big Positive
    O = InputVariable(fuzzify=Plain())
    controller.variables['O'] = O
    O_names = ['Ovbn', 'Obn', 'Osn', 'Oz', 'Osp', 'Obp', 'Ovbp']
    O.adjectives = {name: Adjective(mf) for name, mf in zip(O_names, flat_saw((-3 * pi / 8, 3 * pi / 8), 7))}

    # Create the membership functions to variable w (angular speed).
    # wbn = Big Negative
    # wsn = Small Negative
    # wz  = Near Zero
    # wsp = Small Positive
    # wbp = Big Positive
    w = InputVariable(fuzzify=Plain())
    controller.variables['w'] = w
    w_names = ['wbn', 'wsn', 'wz', 'wsp', 'wbp']
    w.adjectives = {name: Adjective(mf) for name, mf in zip(w_names, flat_saw((-3 * pi, 3 * pi), 5))}

    # Create the membership functions to variable F (Force applied to chart).
    # Fvvbn = Very Very Big Negative
    # Fvbn  = Very Big Negative
    # Fbn   = Big Negative
    # Fsn   = Small Negative
    # Fz    = Near Zero
    # Fsp   = Small Positive
    # Fbp   = Big Positive
    # Fvbp  = Very Big Positive
    # Fvvbp = Very Very Big Positive
    F = OutputVariable(defuzzify=controller.defuzzy())
    controller.variables['F'] = F
    F_names = ['Fvvbn', 'Fvbn', 'Fbn', 'Fsn', 'Fz', 'Fsp', 'Fbp', 'Fvbp', 'Fvvbp']
    F.adjectives = {name: Adjective(mf) for name, mf in zip(F_names, flat_saw((-100., 100.), 9))}

    # Create the controller and insert into it the decision rules. The decision
    # rules are inserted with the use of the add_table method. In this table, each
    # line represents a linguistic value of the O variable; each column represents
    # a linguistic value of the variable w. Each element of the table is the given
    # answer linguistic value of the variable F.
    table_names = [
        ['Fvvbn', 'Fvvbn', 'Fvbn', 'Fbn', 'Fsn'],
        ['Fvvbn', 'Fvbn', 'Fbn', 'Fsn', 'Fz'],
        ['Fvbn', 'Fbn', 'Fsn', 'Fz', 'Fsp'],
        ['Fbn', 'Fsn', 'Fz', 'Fsp', 'Fbp'],
        ['Fsn', 'Fz', 'Fsp', 'Fbp', 'Fvbp'],
        ['Fz', 'Fsp', 'Fbp', 'Fvbp', 'Fvvbp'],
        ['Fsp', 'Fbp', 'Fvbp', 'Fvvbp', 'Fvvbp']
    ]
    controller.add_table([controller.variables['O'].adjectives[name] for name in O_names],
                     [controller.variables['w'].adjectives[name] for name in w_names],
                     [[controller.variables['F'].adjectives[name] for name in row] for row in table_names])

    # Create the membership functions to variable x (cart position).
    x = InputVariable(fuzzify=Plain())
    controller.variables['x'] = x
    x_names = ['xn', 'xz', 'xp']
    x.adjectives = {name: Adjective(mf) for name, mf in zip(x_names, flat_saw((-10., 10.), 3))}

    # Create the membership functions to variable v (cart speed).
    v = InputVariable(fuzzify=Plain())
    controller.variables['v'] = v
    v_names = ['vn', 'vz', 'vp']
    v.adjectives = {name: Adjective(mf) for name, mf in zip(v_names, flat_saw((-6., 6.), 3))}

    # Decision rules for position and speed of the cart. While this worked, the
    # pendulum ended up very unstable.
    table_names = [
        ['Fbp', 'Fbp', 'Fz'],
        ['Fbp', 'Fz', 'Fbn'],
        ['Fz', 'Fbn', 'Fbn']
    ]
    # controller.add_table([controller.variables['x'].adjectives[name] for name in x_names],
    #                  [controller.variables['v'].adjectives[name] for name in v_names],
    #                  [[controller.variables['F'].adjectives[name] for name in row] for row in table_names])

    return controller


PC = create_controller()