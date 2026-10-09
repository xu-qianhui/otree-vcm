import random

from otree.api import Bot, SubmissionMustFail, expect, cu

from . import (
    C,
    group_partition,
    Introduction,
    PhaseChange,
    Contribution,
    Results,
)


class PlayerBot(Bot):
    cases = ['zero', 'full', 'random']

    def play_round(self):
        rn = self.round_number
        subsession = self.subsession

        # MPCR schedule and the social-dilemma condition 1/N < MPCR < 1
        expected_mpcr = C.MPCR_PHASE1 if rn < C.BREAK_ROUND else C.MPCR_PHASE2
        expect(subsession.mpcr, expected_mpcr)
        expect(1 / C.PLAYERS_PER_GROUP < subsession.mpcr < 1, True)

        # Groups fixed within a phase, re-formed at the break
        if rn not in (1, C.BREAK_ROUND):
            prev = self.player.in_round(rn - 1)
            expect(
                sorted(p.participant.code for p in self.group.get_players()),
                sorted(p.participant.code for p in prev.group.get_players()),
            )
        expect(len(self.group.get_players()), C.PLAYERS_PER_GROUP)

        # With more than one group, the partition at the break must differ from phase 1
        if rn == C.BREAK_ROUND and len(subsession.get_groups()) > 1:
            expect(
                group_partition(subsession) != group_partition(subsession.in_round(1)),
                True,
            )

        if rn == 1:
            yield Introduction
        if rn == C.BREAK_ROUND:
            yield PhaseChange

        if self.case == 'zero':
            c = 0
        elif self.case == 'full':
            c = C.ENDOWMENT
        else:
            c = random.randint(0, C.ENDOWMENT)

        yield SubmissionMustFail(Contribution, dict(contribution=-1))
        yield SubmissionMustFail(Contribution, dict(contribution=C.ENDOWMENT + 1))
        yield Contribution, dict(contribution=c)

        # Payoff identity: pi_i = (E - c_i) + MPCR * sum_j c_j
        total = sum(p.contribution for p in self.group.get_players())
        expect(self.group.total_contribution, total)
        expect(self.player.payoff, cu(C.ENDOWMENT - c) + cu(total * subsession.mpcr))
        yield Results

        if rn == C.NUM_ROUNDS:
            # FinalResults is the terminal page (no Next button), so only check its content.
            # self.participant is cached by the bot, so verify the rendered total instead.
            total_payoff = sum(p.payoff for p in self.player.in_all_rounds())
            expect(f'Total earnings over {C.NUM_ROUNDS} rounds: {total_payoff}', 'in', self.html)
