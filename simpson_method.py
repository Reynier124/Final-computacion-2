from sympy import *
import numpy as np

class Simpson:
    def __init__(self, a, b, n):
        self._x = symbols('x')
        self._a = a
        self._b = b
        self._n = n
        self._h = 0

    def has_tan(self, f):
        f = sympify(f)
        return f.has(tan)

    def check_denominator(self, f):
        numerator, denominator = fraction(f)
        return any(denominator.has(trig) for trig in (sin, cos, tan))

    def has_trig_in_denominator(self, f):
        f = sympify(f)
        if isinstance(f, (Add, Mul)):
            terms = f.args
        else:
            terms = [f]
        for term in terms:
            if self.check_denominator(term):
                return True
        return False

    def analyze(self, f):
        f = sympify(f)
        discontinuities = singularities(f, self._x)
        interval = Interval(self._a, self._b)
        if self.has_tan(f) or self.has_trig_in_denominator(f):
            j = 0
            for discontinuity in discontinuities:
                if discontinuity in interval:
                    return True
                if j == self._b:
                    return False
                j += 1
        for discontinuity in discontinuities:
            if discontinuity in interval:
                return True
        return False

    def calculate_points(self):
        points = np.zeros(self._n + 1)
        points[:] = self._a + self._h * np.arange(self._n + 1)
        return points

    def calculate_max_derived_point(self, points, f):
        f_diff = diff(f, self._x, 4)
        y_diff = lambdify(self._x, f_diff)
        dpoints = []
        try:
            y_diff_values = np.array([y_diff(p) for p in points])
        except ZeroDivisionError:
            y_diff_values = np.zeros_like(points)
        dpoints = np.abs(y_diff_values)
        dpoints = np.nan_to_num(dpoints, nan=0.0, posinf=0.0, neginf=0.0)
        return np.max(dpoints)

    def calculate_sum(self, points, y, odd=True):
        indices = np.arange(1, self._n)
        if odd:
            odd_indices = indices[indices % 2 != 0]
            y_odd = np.array([y(points[i]) for i in odd_indices])
            return np.sum(y_odd)
        else:
            even_indices = indices[indices % 2 == 0]
            y_even = np.array([y(points[i]) for i in even_indices])
            return np.sum(y_even)

    def calculate(self, f, aprox=4):
        f = sympify(f)
        self._h = (self._b - self._a) / self._n
        if self.analyze(f):
            return "Integral no valida"

        S = 0
        R = 0

        y = lambdify(self._x, f)
        points = self.calculate_points()

        max_derived = self.calculate_max_derived_point(points, f)
        odd_sum = self.calculate_sum(points, y, True)
        even_sum = self.calculate_sum(points, y, False)

        S = float((y(points[0]) + 4 * odd_sum + 2 * even_sum + y(points[self._n])) / (3 * self._n))
        R = float(-(self._h ** 5 / 90) * max_derived)
        result = round(S + R, aprox)
        simp_aprox = round(S, aprox)
        error_aprox = round(R, aprox)
        return result, simp_aprox, error_aprox
