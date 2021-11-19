# Python imports
from datetime import datetime, timedelta
import json

# Local imports
import complex_encoder
import loan

# Dict key constants
DATE = 'date'
END_DATE = 'end_date'
LOAN = 'loan'
ONE_TIME_PAYMENTS = 'one_time_payments'
PAYMENT = 'payment'
PERIOD = 'period'
RECURRING_PAYMENTS = 'recurring_payments'
START_DATE = 'start_date'

# ISO 8601 format constant
ISO8601_NO_TIME = '%Y-%m-%d'

def convert_datetime_to_string(dt):
    """Convert a datetime object to ISO 8601 format with no time.

    :param datetime dt: The datetime object
    """

    if not isinstance(dt, datetime):
        raise TypeError('Input must be a datetime object.')

    return dt.strftime(ISO8601_NO_TIME)


def convert_string_to_datetime(value):
    """Convert a string in ISO 8601 format with no time to a datetime object.

    :param string value: A string representing a date in ISO 8601 with no time
    """

    if not isinstance(value, str):
        raise TypeError('Start date must be a string.')
    try:
        dt = datetime.strptime(value, ISO8601_NO_TIME)
        return dt
    except ValueError:
        raise ValueError('Start date must be in the form YYYY-MM-DD.')


class Results(object):
    """A class that contains the results of a simulated loan repayment scenario.

    The three lists contain the relevant quantities at each payment cycle. They do
    not add entries for extra payments.
    """

    def __init__(self):
        self.cumulative_interest = []
        self.cumulative_payments = []
        self.remaining_principal = []
        self.total_interest = 0.0
        self.total_length = 0
        self.total_payment = 0.0


class Scenario(object):
    """A class that sets up and simulates a loan repayment.

    A scenario allows for one time and recurring payments. One time payments can
    occur anytime. Recurring payments can be ongoing or have an end date, and they
    can be configured to occur at a frequency other than every payment cycle.
    """

    def __init__(self, loan):
        self._loan = None
        self._start_date = None

        self._one_time_payments = []
        self._recurring_payments = []

        self.loan = loan

    @property
    def loan(self):
        return self._loan
    @loan.setter
    def loan(self, value):
        if not isinstance(value, loan.Loan):
            raise TypeError('Input must be a Loan object from the loan module.')
        self._loan = value

    @property
    def start_date(self):
        return self._start_date
    @start_date.setter
    def start_date(self, value):
        self._start_date = convert_string_to_datetime(value)

    @classmethod
    def from_dict(cls, d):
        """Create a Scenario object from a dict.

        :param dict d: The dict encoding a scenario.
        """

        # A Loan object is required to construct a Scenario object.
        # If this key is not present, then the input is a recursive dict entry.
        if LOAN not in d:
            return d

        l = loan.Loan.from_dict(d[LOAN])
        s = cls(l)
        if START_DATE in d:
            s.start_date = d[START_DATE]
        if ONE_TIME_PAYMENTS in d:
            for pd in d[ONE_TIME_PAYMENTS]:
                s.add_one_time_payment(**pd)
        if RECURRING_PAYMENTS in d:
            for pd in d[RECURRING_PAYMENTS]:
                s.add_recurring_payment(**pd)

        return s

    @classmethod
    def from_json(cls, in_path):
        """Create a Scenario object from a JSON file.

        :param string in_path: Path and file name to input
        """

        with open(in_path, 'r') as f:
            return json.load(f, object_hook=cls.from_dict)

    def add_one_time_payment(self, payment, date):
        """Add a one time payment to the scenario.

        :param float payment: The amount to be paid
        :param string date: The date of the payment, in ISO 8601 without time
        """

        if not isinstance(payment, int) and not isinstance(payment, float):
            raise TypeError('Payment must be numeric.')
        if payment < 0:
            raise ValueError('Payment must be greater than or equal to zero.')

        dt = convert_string_to_datetime(date)
        self._one_time_payments.append({DATE: dt, PAYMENT: payment})

        return

    def add_recurring_payment(self, payment, start_date, end_date='', period=1):
        """Add a recurring payment to the scenario.

        Recurring payments are simulated at the standard payment date. The start and
        end dates only determine which standard payments also apply the recurring
        payment. If no end date is specified, the recurring payment continues until the
        loan is fully paid. The period determines how often the recurring payment is
        applied, where the value specifies how many payment cycles occur between
        recurring payments. A value of 2 thus means that the payment occurs every other
        payment cycle.

        :param float payment: The additional amount over the standard payment to be paid
        :param string start: The date to start applying the payment, in ISO 8601 without time
        :param string end: The date to stop applying the payment, in ISO 8601 without time; optional
        :param int period: How often the payment is applied in relation to the standard cycle
        """

        if not isinstance(payment, int) and not isinstance(payment, float):
            raise TypeError('Payment must be numeric.')
        if payment < 0:
            raise ValueError('Payment must be greater than or equal to zero.')

        dt_start = convert_string_to_datetime(start_date)
        dt_end = self.start_date + timedelta(days=365 * self.loan.length)
        if end_date:
            dt_end = convert_string_to_datetime(end_date)

        if not isinstance(period, int):
            raise TypeError('Period must be an integer.')
        if period <= 0:
            raise ValueError('Period must be greater than zero.')

        self._recurring_payments.append(
            {
                END_DATE: dt_end,
                PAYMENT: payment,
                PERIOD: period,
                START_DATE: dt_start,
            }
        )

        return

    def run_scenario(self):
        """Run the repayment simulation, tracking the results in a Results object.
        """

        results = Results()

        frequency = self.loan.frequency
        rate = self.loan.rate
        remaining_principal = self.loan.principal
        current_sim_date = self.start_date
        standard_payment = self.loan.payment
        
        results.cumulative_interest.append(0.0)
        results.cumulative_payments.append(0.0)
        results.remaining_principal.append(remaining_principal)

        unprocessed = 'unprocessed'
        for payment_dict in self._one_time_payments:
            payment_dict[unprocessed] = True

        last = 'last'
        for payment_dict in self._recurring_payments:
            payment_dict[last] = 1

        while remaining_principal >= 0.01:
            current_sim_date += timedelta(365.25 / frequency)
            extra_payments = 0.0

            for payment_dict in self._one_time_payments:
                if payment_dict[DATE] < current_sim_date and unprocessed in payment_dict:
                    extra_payments += payment_dict[PAYMENT]
                    remaining_principal -= payment_dict[PAYMENT]
                    del payment_dict[unprocessed]

            interest = self.loan.interest(remaining_principal, rate, frequency)
            principal_payment = standard_payment - interest
            if principal_payment > remaining_principal:
                principal_payment = remaining_principal
            remaining_principal -= principal_payment

            if remaining_principal >= 0.01:
                for payment_dict in self._recurring_payments:
                    if (
                        payment_dict[START_DATE] <= current_sim_date and
                        current_sim_date <= payment_dict[END_DATE]
                    ):
                        if payment_dict[last] >= payment_dict[PERIOD]:
                            extra_payments += payment_dict[PAYMENT]
                            remaining_principal -= payment_dict[PAYMENT]
                            payment_dict[last] = 1
                        else:
                            payment_dict[last] += 1

            results.cumulative_interest.append(results.cumulative_interest[-1] + interest)
            results.cumulative_payments.append(
                results.cumulative_payments[-1] + standard_payment + extra_payments
            )
            results.remaining_principal.append(remaining_principal)
            results.total_length += 1

        results.total_interest = results.cumulative_interest[-1]
        results.total_payment = results.cumulative_payments[-1]

        for payment_dict in self._one_time_payments:
            if unprocessed in payment_dict:
                del payment_dict[unprocessed]
        for payment_dict in self._recurring_payments:
            if last in payment_dict:
                del payment_dict[last]

        return results

    def to_dict(self):
        """Convert a Scenario object to a dict.
        """

        def convert_all_datetimes_to_strings(ld):
            return [
                {
                    k: v if not isinstance(v, datetime) else convert_datetime_to_string(v)
                    for k, v in d.items()
                }
                for d in ld
            ]

        return {
            LOAN: self.loan,
            ONE_TIME_PAYMENTS: convert_all_datetimes_to_strings(self._one_time_payments),
            RECURRING_PAYMENTS: convert_all_datetimes_to_strings(self._recurring_payments),
            START_DATE: convert_datetime_to_string(self.start_date),
        }

    def to_json(self, out_path, pretty_print=False):
        """Serialize the object to disk as JSON.

        :param string out_path: Path and file name for output
        :param bool pretty_print: Whether to write the JSON in a more readable format
        """

        kwargs = {'cls': complex_encoder.ComplexEncoder, 'sort_keys': True}
        if pretty_print:
            kwargs['indent'] = 4

        with open(out_path, 'w+') as f:
            json.dump(self.to_dict(), f, **kwargs)

        return True
