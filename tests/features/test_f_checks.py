from pytest_bdd import scenario, given, when, then
from checks.checks import Session


@scenario(
    'checks.feature', 'Creation of a Check',
    example_converters=dict(
        formula=str,
        name=str,
        tolerance=float,
        opeartor=str,
    )
)
def test_zero():
    pass


@given('I have a <formula>')
def formula(formula):
    pass


@given('I have a unique <name>')
def name(name):
    pass


@given('I have a <tolerance>')
def tolerance(tolerance):
    pass


@given('I have an <operator>')
def operator(operator):
    pass


@when('I create it on the system')
def create(formula, name, tolerance, operator):
    session = Session()
    session.close()


@then('I can look after it by <name>')
def lookup(name):
    assert name == name
