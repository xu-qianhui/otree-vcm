from otree.api import *


doc = """
Voluntary contribution mechanism (linear public goods game).
Groups of N players, each with endowment E, choose contributions c_i in [0, E].
Payoff: pi_i = (E - c_i) + MPCR * sum_j c_j.
Structural break at C.BREAK_ROUND: the MPCR changes and groups are randomly re-formed.
Within each phase, group composition is fixed (partner matching).
"""


class C(BaseConstants):
    NAME_IN_URL = 'assign2'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 10
    ENDOWMENT = 20  # points; contributions are whole points
    BREAK_ROUND = 6  # first round of phase 2
    MPCR_PHASE1 = 0.4
    MPCR_PHASE2 = 0.8


class Subsession(BaseSubsession):
    phase = models.IntegerField()
    mpcr = models.FloatField()


class Group(BaseGroup):
    total_contribution = models.IntegerField()
    individual_share = models.CurrencyField()


class Player(BasePlayer):
    contribution = models.IntegerField(
        min=0,
        max=C.ENDOWMENT,
        label="How many points will you contribute to the group project?",
    )


# FUNCTIONS
def creating_session(subsession: Subsession):
    if subsession.round_number < C.BREAK_ROUND:
        subsession.phase = 1
        subsession.mpcr = C.MPCR_PHASE1
    else:
        subsession.phase = 2
        subsession.mpcr = C.MPCR_PHASE2

    # Re-form groups at the start of each phase; keep them fixed within a phase
    if subsession.round_number == 1:
        subsession.group_randomly()
    elif subsession.round_number == C.BREAK_ROUND:
        # A random draw can reproduce the phase-1 partition (1 in 10 with 6 players),
        # so redraw until the composition actually changes. With a single group
        # in the session no different partition exists, so stop after a fixed number of draws.
        phase1 = group_partition(subsession.in_round(1))
        for _ in range(100):
            subsession.group_randomly()
            if group_partition(subsession) != phase1:
                break
    else:
        subsession.group_like_round(subsession.round_number - 1)


def group_partition(subsession: Subsession):
    return {
        frozenset(p.participant.id_in_session for p in g.get_players())
        for g in subsession.get_groups()
    }


def phase_first_round(subsession: Subsession):
    return 1 if subsession.phase == 1 else C.BREAK_ROUND


def set_payoffs(group: Group):
    players = group.get_players()
    group.total_contribution = sum(p.contribution for p in players)
    group.individual_share = cu(group.total_contribution * group.subsession.mpcr)
    for p in players:
        p.payoff = cu(C.ENDOWMENT - p.contribution) + group.individual_share


def common_vars(player: Player):
    """Variables shown in the information bar on every page."""
    subsession = player.subsession
    return dict(
        phase=subsession.phase,
        phase_start=phase_first_round(subsession),
        phase_end=C.BREAK_ROUND - 1 if subsession.phase == 1 else C.NUM_ROUNDS,
        mpcr=subsession.mpcr,
        endowment=C.ENDOWMENT,
        group_size=C.PLAYERS_PER_GROUP,
        num_rounds=C.NUM_ROUNDS,
        break_round=C.BREAK_ROUND,
        phase1_end=C.BREAK_ROUND - 1,
        mpcr_phase1=C.MPCR_PHASE1,
        mpcr_phase2=C.MPCR_PHASE2,
    )


def phase_history(player: Player):
    """Completed rounds of the current phase (same group as now)."""
    start = phase_first_round(player.subsession)
    if player.round_number == start:
        return []
    return [
        dict(
            round_number=p.round_number,
            contribution=p.contribution,
            total_contribution=p.group.total_contribution,
            payoff=p.payoff,
        )
        for p in player.in_rounds(start, player.round_number - 1)
    ]


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # Worked example: you contribute 5, the others contribute 10 in total
        own, others = 5, 10
        total = own + others
        return dict(
            **common_vars(player),
            ex_own=own,
            ex_others=others,
            ex_total=total,
            ex_kept=cu(C.ENDOWMENT - own),
            ex_share=cu(total * C.MPCR_PHASE1),
            ex_payoff=cu(C.ENDOWMENT - own) + cu(total * C.MPCR_PHASE1),
        )


class PhaseChange(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.BREAK_ROUND

    @staticmethod
    def vars_for_template(player: Player):
        return common_vars(player)


class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(**common_vars(player), history=phase_history(player))

    @staticmethod
    def js_vars(player: Player):
        return dict(
            endowment=C.ENDOWMENT,
            mpcr=player.subsession.mpcr,
            group_size=C.PLAYERS_PER_GROUP,
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        others = [p.contribution for p in player.get_others_in_group()]
        return dict(
            **common_vars(player),
            endowment_kept=cu(C.ENDOWMENT - player.contribution),
            others_contributions=others,
            others_total=sum(others),
            is_last_before_break=player.round_number == C.BREAK_ROUND - 1,
            is_last_round=player.round_number == C.NUM_ROUNDS,
        )


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        rounds = [
            dict(
                round_number=p.round_number,
                phase=p.subsession.phase,
                mpcr=p.subsession.mpcr,
                contribution=p.contribution,
                total_contribution=p.group.total_contribution,
                payoff=p.payoff,
            )
            for p in player.in_all_rounds()
        ]
        return dict(
            **common_vars(player),
            rounds=rounds,
            total_payoff=player.participant.payoff,
        )


page_sequence = [
    Introduction,
    PhaseChange,
    Contribution,
    ResultsWaitPage,
    Results,
    FinalResults,
]
