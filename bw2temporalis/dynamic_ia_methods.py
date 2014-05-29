from .utils import get_maximum_value
from bw2data import DataStore, Method
from bw2data.serialization import SerializedDict
from bw2data.utils import random_string
import itertools
import warnings


class DynamicMethods(SerializedDict):
    """A dictionary for dynamic impact assessment method metadata. File data is saved in ``dynamic-methods.json``."""
    filename = "dynamic-methods.json"


dynamic_methods = DynamicMethods()


class DynamicIAMethod(DataStore):
    """A dynamic impact assessment method. Not translated into matrices, so no ``process`` method."""
    metadata = dynamic_methods

    def process(self):
        """Dynamic CFs can't be translated into a matrix, so this is a no-op."""
        warnings.warn("Dynamic CFs can't be processed; doing nothing")
        return

    def to_worst_case_method(self, name, lower=None, upper=None):
        """Create a static LCA method using the worst case for each dynamic CF function.

        Default time interval over which to test for maximum CF is 2000 to 2100."""
        kwargs = {}
        if lower is not None:
            kwargs['lower'] = lower
        if upper is not None:
            kwargs['upper'] = upper
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            worst_case_method = Method(tuple(name))
            worst_case_method.register(dynamic_method = self.name)
        data = self.load()
        data.update(**self.create_functions())
        worst_case_method.write([
            [key, abs(get_maximum_value(value, **kwargs))]
            for key, value in data.iteritems()
        ])
        worst_case_method.process()
        return worst_case_method

    def create_functions(self, data=None):
        """Take method data that defines functions in strings, and turn them into actual Python code. Returns a dictionary with flows as keys and functions as values."""
        if data is None:
            data = self.load()
        counter = itertools.count()
        prefix = u"created_function_%s_" % random_string()
        functions = {}
        for key, value in data.iteritems():
            if isinstance(value, basestring):
                name = prefix + str(counter.next())
                value = value % name
                exec(value)
                functions[key] = locals()[name]
        return functions
