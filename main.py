#!/usr/bin/env python3
from operator import itemgetter

import pandas as pd
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


def main():
    date = input()
    team_H = input()
    team_A = input()

    Teams_to_predict = [team_H, team_A]

    # load data from csv
    football_data = pd.read_csv("data.csv", header=0, usecols=[0, 1, 2, 3, 4, 5],
                                names=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])

    # read results 2 last team matches
    Teams_Matches = [0, 0]
    for j in range(2):
        Matches = []
        for i in range(football_data.last_valid_index() + 1):
            if football_data["HomeTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "H":
                    Matches.append(0)
                elif football_data["FTR"][i] == "D":
                    Matches.append(2)
                elif football_data["FTR"][i] == "A":
                    Matches.append(1)
            elif football_data["AwayTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "A":
                    Matches.append(0)
                elif football_data["FTR"][i] == "D":
                    Matches.append(2)
                elif football_data["FTR"][i] == "H":
                    Matches.append(1)

        # 2 last matches: Previous -> [0], Current [1]
        Matches.reverse()
        del Matches[2:]
        Teams_Matches[j] = Matches
    print(Teams_Matches)

    # create a list of teams
    Teams = []
    team_list = football_data.copy()
    team_list.sort_values(["HomeTeam"], inplace=True)
    team_list.drop_duplicates(subset=['HomeTeam'], keep='last', inplace=True)
    team_list.reset_index(inplace=True)
    for i in range(team_list.last_valid_index() + 1):
        Teams.append(team_list["HomeTeam"][i])

    # counting team's goals and results
    Ranking = []

    # loop for Teams
    for j in range(team_list.last_valid_index() + 1):
        goals_home = 0
        goals_away = 0
        losses_home = 0
        losses_away = 0
        # loop for football_data
        for i in range(football_data.last_valid_index() + 1):
            if football_data["HomeTeam"][i] == Teams[j]:
                goals_home += (football_data["FTHG"][i])
                losses_home += (football_data["FTAG"][i])
            elif football_data["AwayTeam"][i] == Teams[j]:
                goals_away += (football_data["FTAG"][i])
                losses_away += (football_data["FTHG"][i])
        # counting team's goals ans losses
        goals = goals_home + goals_away
        losses = losses_home + losses_away
        # Ranking = [name, G, GH, GA, L, LH, LA]
        Ranking.append((Teams[j], goals, goals_home, goals_away, losses, losses_home, losses_away))

    # Create ranking [('TeamName', Goals, Losses)] sorted by goals and losses
    Half_Sorted_Ranking = sorted(Ranking, key=itemgetter(4), reverse=False)
    Sorted_Ranking = sorted(Half_Sorted_Ranking, key=itemgetter(1), reverse=True)
    print(Sorted_Ranking)

    # ------------------------------------------------------------------
    # create efficiency prob
    home_efficiency = 0
    away_efficiency = 0

    for i in range(len(Sorted_Ranking)):
        if Sorted_Ranking[i][0] == Teams_to_predict[0]:
            home_efficiency = 0.2 - i * 0.015

        elif Sorted_Ranking[i][0] == Teams_to_predict[1]:
            away_efficiency = 0.2 - i * 0.015

    teams_eff = [home_efficiency, away_efficiency]

    # Create the model with edges specified as tuples (parent, child)
    edges = []
    for i in range(2):
        edges.append(('Eff_0' + str(i), 'Eff_prev' + str(i)))
        edges.append(('Eff_prev' + str(i), 'Eff_curr' + str(i)))
        edges.append(('Eff_curr' + str(i), 'Eff_predict' + str(i)))

        edges.append(('Eff_prev' + str(i), 'Result_prev' + str(i)))
        edges.append(('Eff_curr' + str(i), 'Result_curr' + str(i)))

    football_model = BayesianModel(edges)

    # Create tabular CPDs, values has to be 2-D array
    cpd_e0 = []
    cpd_eff_prev = []
    cpd_eff_curr = []
    cpd_eff_predict = []

    cpd_result_prev = []
    cpd_result_curr = []

    for i in range(2):
        cpd_e0.append(TabularCPD(variable='Eff_0' + str(i),
                                 variable_card=2,
                                 values=[[0.6], [0.4]]))

        cpd_eff_prev.append(TabularCPD(variable='Eff_prev' + str(i),
                                       variable_card=2,
                                       values=[[0.9, 0.1], [0.1, 0.9]],
                                       evidence=['Eff_0' + str(i)],
                                       evidence_card=[2]))

        cpd_eff_curr.append(TabularCPD(variable='Eff_curr' + str(i),
                                       variable_card=2,
                                       values=[[0.9, 0.1], [0.1, 0.9]],
                                       evidence=['Eff_prev' + str(i)],
                                       evidence_card=[2]))

        cpd_eff_predict.append(TabularCPD(variable='Eff_predict' + str(i),
                                          variable_card=2,
                                          values=[[0.9, 0.1], [0.1, 0.9]],
                                          evidence=['Eff_curr' + str(i)],
                                          evidence_card=[2]))

        cpd_result_prev.append(TabularCPD(variable='Result_prev' + str(i),
                                          variable_card=3,
                                          values=[[0.85, 0.1], [0.1, 0.8], [0.05, 0.1]],
                                          evidence=['Eff_prev' + str(i)],
                                          evidence_card=[2]))

        cpd_result_curr.append(TabularCPD(variable='Result_curr' + str(i),
                                          variable_card=3,
                                          values=[[0.85, 0.1], [0.1, 0.8], [0.05, 0.1]],
                                          evidence=['Eff_curr' + str(i)],
                                          evidence_card=[2]))

    # Add CPDs to model
    football_model.add_cpds(*cpd_e0, *cpd_eff_prev, *cpd_eff_curr, *cpd_eff_predict, *cpd_result_prev, *cpd_result_curr)

    # print('Check model :', football_model.check_model())
    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)

    qH = football_infer.query(['Eff_predict0'],
                              evidence={'Result_prev0': Teams_Matches[0][0], 'Result_curr0': Teams_Matches[0][1]},
                              show_progress=False)
    print('P(Eff_predict0|Results=\n', qH)
    qA = football_infer.query(['Eff_predict1'],
                              evidence={'Result_prev1': Teams_Matches[1][0], 'Result_curr1': Teams_Matches[1][1]},
                              show_progress=False)
    print('P(Eff_predict1|Results=\n', qA)

    # qH = football_infer.query(['Eff_predict0'], evidence={'Result_prev0': 2, 'Result_curr0': 2}, show_progress=False)
    # print('P(Eff_predict0|Results=\n', qH)
    # qA = football_infer.query(['Eff_predict1'], evidence={'Result_prev1': 0, 'Result_curr1': 1}, show_progress=False)
    # print('P(Eff_predict1|Results=\n', qA)

    good_eff_H = qH.values[0]
    good_eff_H += teams_eff[0]

    good_eff_A = qA.values[0]
    good_eff_A += teams_eff[1]

    sub = abs(good_eff_A - good_eff_H)

    print('Sub: ', sub)
    print('Home: ', good_eff_H)
    print('Away: ', good_eff_A)

    if sub > 0.1:
        if good_eff_H > good_eff_A:
            print('H')
        else:
            print('A')
    else:
        print('D')


if __name__ == '__main__':
    main()
