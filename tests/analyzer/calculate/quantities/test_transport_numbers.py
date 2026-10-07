"""TransportNumbers: the share of the charge lithium and magnesium each carried."""

import pytest

from limodel.analyzer.calculate.quantities.transport_numbers import TransportNumbers


@pytest.fixture
def crossed_ten_millimoles_of_each(a_sampled_reading):
    """1.000 L both ends, so mg/L reads as mg: 69.4 mg of Li and 243.05 mg of Mg crossed.

    That is 10 mmol of each, and Mg carries two charges, so Li holds 10 of the 30.
    """
    return (a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0, mg_mg_l=0),
            a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4, mg_mg_l=243.05))


def test_it_finds_the_share_lithium_carried(a_run, crossed_ten_millimoles_of_each):
    """10 of the 30 charges, which is a third."""
    run = a_run(tank_readings=crossed_ten_millimoles_of_each)

    t_li, _ = TransportNumbers.find_numbers(run)

    assert t_li == pytest.approx(1 / 3)


def test_it_finds_the_share_magnesium_carried(a_run, crossed_ten_millimoles_of_each):
    """20 of the 30 charges, because every magnesium ion carries two."""
    run = a_run(tank_readings=crossed_ten_millimoles_of_each)

    _, t_mg = TransportNumbers.find_numbers(run)

    assert t_mg == pytest.approx(2 / 3)


def test_the_two_shares_are_the_whole_charge(a_run, crossed_ten_millimoles_of_each):
    run = a_run(tank_readings=crossed_ten_millimoles_of_each)

    t_li, t_mg = TransportNumbers.find_numbers(run)

    assert t_li + t_mg == pytest.approx(1.0)


def test_equal_millimoles_do_not_mean_equal_shares(a_run, crossed_ten_millimoles_of_each):
    """The point of weighting by charge: 10 mmol each is a third against two thirds."""
    run = a_run(tank_readings=crossed_ten_millimoles_of_each)

    t_li, t_mg = TransportNumbers.find_numbers(run)

    assert t_li != pytest.approx(t_mg)


def test_a_run_that_let_little_magnesium_through_is_mostly_lithium(a_run, a_sampled_reading):
    """10 mmol of Li against 1 mmol of Mg is 10 charges of 12."""
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=0),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=24.305)))

    t_li, t_mg = TransportNumbers.find_numbers(run)

    assert t_li == pytest.approx(10 / 12)
    assert t_mg == pytest.approx(2 / 12)


def test_a_metal_the_lab_never_reported_leaves_no_numbers(a_run, a_sampled_reading):
    """Magnesium missing means the shares would not add to the whole charge."""
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=None),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=None)))

    assert TransportNumbers.find_numbers(run) is None


def test_one_sampled_minute_leaves_no_numbers(a_run, a_sampled_reading):
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=69.4,
                                                 mg_mg_l=243.05),))

    assert TransportNumbers.find_numbers(run) is None


def test_a_run_with_no_readings_at_all_is_not_an_error(a_run):
    assert TransportNumbers.find_numbers(a_run()) is None


def test_nothing_crossing_leaves_no_shares_to_hand_out(a_run, a_sampled_reading):
    """Both ends read zero, so there is no charge to take a share of."""
    run = a_run(tank_readings=(a_sampled_reading(minute=0, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=0),
                               a_sampled_reading(minute=60, weight_g=1100, li_mg_l=0,
                                                 mg_mg_l=0)))

    assert TransportNumbers.find_numbers(run) is None
