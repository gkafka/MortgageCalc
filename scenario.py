# Python imports
from datetime import datetime, timedelta
from typing import Type

import loan

DATE = 'date'
END_DATE = 'end date'
LAST = 'last'
PAYMENT = 'payment'
PERIOD = 'period'
PROCESSED = 'processed'
START_DATE = 'start date'

def validate_and_convert_string_to_datetime(value):
    """Verify a string is ISO 8601 format with no time and convert it to a datetime.

    :param string value: A string representing a date in ISO 8601 with no time
    """

    if not isinstance(value, str):
        raise TypeError('Start date must be a string.')
    try:
        dt = datetime.strptime(value, '%Y-%m-%d')
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
        self._start_date = validate_and_convert_string_to_datetime(value)

    def add_one_time_payment(self, payment, date):
        """Add a one time payment to the scenario.

        :param float payment: The amount to be paid
        :param string date: The date of the payment, in ISO 8601 without time
        """

        if not isinstance(payment, int) and not isinstance(payment, float):
            raise TypeError('Payment must be numeric.')
        if payment < 0:
            raise ValueError('Payment must be greater than or equal to zero.')

        dt = validate_and_convert_string_to_datetime(date)
        self._one_time_payments.append({DATE: dt, PAYMENT: payment, PROCESSED: False})

        return

    def add_recurring_payment(self, payment, start, end='', period=1):
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

        dt_start = validate_and_convert_string_to_datetime(start)
        dt_end = datetime.now() + timedelta(days=365)
        if end:
            dt_end = validate_and_convert_string_to_datetime(end)

        if not isinstance(period, int):
            raise TypeError('Period must be an integer.')
        if period <= 0:
            raise ValueError('Period must be greater than zero.')

        self._recurring_payments.append(
            {
                END_DATE: dt_end,
                LAST: 1,
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

        while remaining_principal >= 0.01:
            current_sim_date += timedelta(365.25 / frequency)
            extra_payments = 0.0

            for payment_dict in self._one_time_payments:
                if payment_dict[DATE] < current_sim_date and not payment_dict[PROCESSED]:
                    extra_payments += payment_dict[PAYMENT]
                    remaining_principal -= payment_dict[PAYMENT]
                    payment_dict[PROCESSED] = True

            interest = self.loan.interest(remaining_principal, rate, frequency)
            principal_payment = standard_payment - interest
            if principal_payment > remaining_principal:
                principal_payment = remaining_principal
            remaining_principal -= principal_payment

            for payment_dict in self._recurring_payments:
                if (
                    payment_dict[START_DATE] <= current_sim_date and
                    current_sim_date <= payment_dict[END_DATE]
                ):
                    if payment_dict[LAST] >= payment_dict[PERIOD]:
                        extra_payments += payment_dict[PAYMENT]
                        remaining_principal -= payment_dict[PAYMENT]
                        payment_dict[LAST] = 1
                    else:
                        payment_dict[LAST] += 1

            results.cumulative_interest.append(results.cumulative_interest[-1] + interest)
            results.cumulative_payments.append(
                results.cumulative_payments[-1] + standard_payment + extra_payments
            )
            results.remaining_principal.append(remaining_principal)
            results.total_length += 1

        results.total_interest = results.cumulative_interest[-1]
        results.total_payment = results.cumulative_payments[-1]

        return results
