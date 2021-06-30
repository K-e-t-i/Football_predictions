#!/usr/bin/env python3
from operator import itemgetter

import pandas as pd
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


def make_dictH(matches):
    list_dictionaryH = {}
    for i in range(4):
        list_dictionaryH['Match0' + str(i)] = matches[0][i]
    list_dictionaryH['Efficiency0'] = 0
    list_dictionaryH['Venue0'] = 0
    return list_dictionaryH


def make_dictA(matches):
    list_dictionaryA = {}
    for i in range(4):
        list_dictionaryA['Match1' + str(i)] = matches[1][i]
    list_dictionaryA['Efficiency1'] = 0
    list_dictionaryA['Venue1'] = 1
    return list_dictionaryA


def main():
    date = input()
    team_H = input()
    team_A = input()

    Teams_to_predict = [team_H, team_A]

    # load data from csv
    football_data = pd.read_csv("data.csv", header=0, usecols=[0, 1, 2, 3, 4, 5],
                                names=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])

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
    # print(Sorted_Ranking)

    # ------------------------------------------------------------------

    # create efficiency prob
    for i in range(len(Sorted_Ranking)):
        if Sorted_Ranking[i][0] == Teams_to_predict[0]:
            eff_AH = 0.9 - i * 0.02
            eff_AD = 0.4 + i * 0.01
            if Sorted_Ranking[i][2] > Sorted_Ranking[i][3]:
                eff_AH += 0.05

        elif Sorted_Ranking[i][0] == Teams_to_predict[1]:
            eff_BA = 0.9 - i * 0.02
            eff_BD = 0.6 + i * 0.01
            if Sorted_Ranking[i][2] < Sorted_Ranking[i][3]:
                eff_BA += 0.05

    eff = [eff_AH, eff_BA]
    eff_D = [eff_AD, eff_BD]

    # read results 4 last team matches
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

        # 4 last matches: Last -> [0], One before last [1], Earlier [2], The Earliest [3]
        Matches.reverse()
        del Matches[4:]
        Teams_Matches[j] = Matches
    # print(Teams_Matches)

    # ------------------------------------------------------------------

    # Create the model with edges specified as tuples (parent, child)
    edges = []
    for i in range(2):
        edges.append(('Team' + str(i), 'Efficiency' + str(i)))
        edges.append(('Team' + str(i), 'Run' + str(i)))
        edges.append(('Team' + str(i), 'Venue' + str(i)))

        for j in range(4):
            edges.append(('Run' + str(i), 'Match' + str(i) + str(j)))

    football_model = BayesianModel(edges)

    # Create tabular CPDs, values has to be 2-D array
    cpd_run = []
    cpd_efficiency = []
    cpd_venue = []
    cpd_team = []
    cpd_match = []

    for i in range(2):
        cpd_run.append(TabularCPD('Run' + str(i), 3, [[0.75, 0.1], [0.05, 0.1], [0.2, 0.8]], evidence=['Team' + str(i)],
                                  evidence_card=[2]))

        cpd_efficiency.append(
            TabularCPD('Efficiency' + str(i), 2, [[eff[i], eff_D[i]], [1 - eff[i], 1 - eff_D[i]]],
                       evidence=['Team' + str(i)],
                       evidence_card=[2]))

        cpd_venue.append(TabularCPD('Venue' + str(i), 2, [[0.55, 0.45], [0.45, 0.55]], evidence=['Team' + str(i)],
                                    evidence_card=[2]))
        cpd_team.append(TabularCPD('Team' + str(i), 2, [[0.5], [0.5]]))

        for j in range(4):
            cpd_match.append(
                TabularCPD('Match' + str(i) + str(j), 3,
                           [[0.6 - i * 0.05, 0.1 + i * 0.05, 0.3], [0.2 + i * 0.05, 0.6 - i * 0.05, 0.3],
                            [0.2, 0.3, 0.4]],
                           evidence=['Run' + str(i)],
                           evidence_card=[3]))

    # Add CPDs to model
    football_model.add_cpds(*cpd_run, *cpd_efficiency, *cpd_venue, *cpd_team, *cpd_match)

    # print('Check model :', football_model.check_model())

    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)

    qH = football_infer.query(['Team0'], evidence=make_dictH(Teams_Matches), show_progress=False)
    winH = qH.values[0]
    drawH = qH.values[1]

    qA = football_infer.query(['Team1'], evidence=make_dictA(Teams_Matches), show_progress=False)
    winA = qA.values[0]
    drawA = qA.values[1]

    sub = abs(winH - winA)

    # preset results
    if drawH > 0.4 and drawA > 0.4 or sub < 0.15:
        print("D")
    elif winH > winA and sub > 0.15:
        print("H")
    elif winA > winH and sub > 0.15:
        print("A")


if __name__ == '__main__':
    main()
