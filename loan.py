# Python imports
import json

# Local imports
import complex_encoder

FREQUENCY = 'frequency'
LENGTH = 'length'
PAYMENT = 'payment'
PRINCIPAL = 'principal'
RATE = 'rate'


class Loan(object):
    """A class that encodes information about a loan and calculates other relevant
    information based on current values.

    Member variables and definitions:
    frequency: Number of loan payments per year
    length: Total length of the loan in years
    payment: Required payment at the end of each loan cycle
    principal: Total loan amount at the loan start
    rate: The annual rate of the loan (not APR) expressed as a ratio
    """

    def __init__(self):
        self._frequency = 0
        self._length = 0
        self._payment = 0.0
        self._principal = 0.0
        self._rate = -1.0

    @property
    def frequency(self):
        return self._frequency
    @frequency.setter
    def frequency(self, value):
        if not isinstance(value, int):
            raise TypeError('Frequency must be an integer.')
        if value <= 0:
            raise ValueError('Frequency must be greater than zero.')
        self._frequency = value

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, value):
        if not isinstance(value, int):
            raise TypeError('Length must be an integer.')
        if value <= 0:
            raise ValueError('Length must be greater than zero.')
        self._length = value

    @property
    def payment(self):
        return self._payment
    @payment.setter
    def payment(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError('Payment must be numeric.')
        if value < 0:
            raise ValueError('Payment must be greater than or equal to zero.')
        self._payment = value

    @property
    def principal(self):
        return self._principal
    @principal.setter
    def principal(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError('Principal must be numeric.')
        if value < 0:
            raise ValueError('Principal must be greater than or equal to zero.')
        self._principal = value

    @property
    def rate(self):
        return self._rate
    @rate.setter
    def rate(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            raise TypeError('Rate must be numeric.')
        if value < 0:
            raise ValueError('Rate must be greater than or equal to zero.')
        self._rate = value

    @staticmethod
    def interest(principal, rate, frequency):
        """Calculate the interest charged per loan cycle.

        :param float principal: The loan principal
        :param float rate: The annual rate of the loan (not APR) as a ratio
        :param int frequency: The number of loan payments per year
        """

        if frequency <= 0:
            raise ValueError('Frequnecy must be greater than zero.')
        if principal < 0:
            raise ValueError('Principal must be greater than or equal to zero.')
        if rate < 0:
            raise ValueError('Rate must be greater than or equal to zero.')

        return round(principal * (rate / frequency), 2)

    @staticmethod
    def calculate_form_factor(frequency, length, rate):
        """Make a standard calculation necessary in multiple calculation types.

        :param int frequency: The number of loan payments per year
        :param int length: The length of the loan in years
        :param float rate: The annual rate of the loan (not APR) as a ratio
        """

        if frequency <= 0:
            raise ValueError('Frequnecy must be greater than zero.')
        if length <= 0:
            raise ValueError('Length must be greater than zero.')
        if rate < 0:
            raise ValueError('Rate must be greater than or equal to zero.')

        n = length * frequency

        if rate == 0:
            return 1 / n

        r = rate / frequency
        f = (1 + r) ** n
        return f * r / (f - 1)

    def calculate_payment(self, store_result=False):
        """Calculate the amount charged per loan cycle based on the loan frequency,
        length, principal and rate.

        :param bool store_result: Whether to save the result to the class variable
        """

        if not self._check_required_inputs(ignore_principal=True):
            raise RuntimeError('All necessary variables have not been set.')

        payment = self.principal * self.calculate_form_factor(
            self.frequency, self.length, self.rate
        )
        payment = round(payment, 2)

        if store_result:
            self.payment = payment

        return payment

    def calculate_principal(self, store_result=False):
        """Calculate the total loan principal based on the loan frequency, length,
        payment per loan cycle and rate.

        :param bool store_result: Whether to save the result to the class variable
        """

        if not self._check_required_inputs(ignore_payment=True):
            raise RuntimeError('All necessary variables have not been set.')

        principal = self.payment / self.calculate_form_factor(
            self.frequency, self.length, self.rate
        )
        principal = round(principal, 2)

        if store_result:
            self.principal = principal

        return principal

    def to_dict(self):
        """Convert a Loan object to a dict.
        """

        return {
            FREQUENCY: self.frequency,
            LENGTH: self.length,
            PAYMENT: self.payment,
            PRINCIPAL: self.principal,
            RATE: self.rate,
        }

    def write(self, out_path, pretty_print=False):
        """Serialize the object to disk.

        :param string out_path: Path and file name for output
        :param bool pretty_print: Whether to write the JSON in a more readable format
        """

        kwargs = {'cls': complex_encoder.ComplexEncoder, 'sort_keys': True}
        if pretty_print:
            kwargs['indent'] = 4

        with open(out_path, 'w+') as f:
            json.dump(self.to_dict(), f, **kwargs)

        return True

    def _check_required_inputs(self, ignore_payment=True, ignore_principal=True):
        """Check that inputs required for calculations have been set.

        :param bool ignore_payment: Whether to skip checking the class variable payment 
        :param bool ignore_principal: Whether to skip checking the class variable principal 
        """

        if self.frequency <= 0:
            return False
        if self.length <= 0:
            return False
        if self.rate < 0:
            return False
        if not ignore_payment and self.payment <= 0:
            return False
        if not ignore_principal and self.principal <= 0:
            return False

        return True
