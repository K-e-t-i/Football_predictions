#!/usr/bin/env python3
from operator import itemgetter

import pandas as pd
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


def main():
    # date = input("Podaj datę meczu: ")
    # hometeam = input("Podaj nazwę drużyny gospodarzy: ")
    # awayteam = input("Podaj nazwę drużyny grającej na wyjeździe: ")

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

    # Create ranking [('TeamName', Goals, Losses)]
    Half_Sorted_Ranking = sorted(Ranking, key=itemgetter(4), reverse=False)
    Sorted_Ranking = sorted(Half_Sorted_Ranking, key=itemgetter(1), reverse=True)
    print(Sorted_Ranking)

    # ------------------------------------------------------------------

    team_A = "Liverpool"
    team_B = "Fulham"
    eff_H = []
    eff_A = []
    eff_D = []

    for i in range(len(Sorted_Ranking)):
        if Sorted_Ranking[i][0] == team_A:
            eff_AH = 0.9 - i * 0.03
            eff_AA = 0.9 - i * 0.03
            eff_AD = 0.6 + i * 0.01
            if Sorted_Ranking[i][2] > Sorted_Ranking[i][3]:
                eff_AH += 0.05
            elif Sorted_Ranking[i][2] < Sorted_Ranking[i][3]:
                eff_AA += 0.05

        elif Sorted_Ranking[i][0] == team_B:
            eff_BH = 0.9 - i * 0.03
            eff_BA = 0.9 - i * 0.03
            eff_BD = 0.6 + i * 0.01
            if Sorted_Ranking[i][2] > Sorted_Ranking[i][3]:
                eff_BH += 0.05
            elif Sorted_Ranking[i][2] < Sorted_Ranking[i][3]:
                eff_BA += 0.05
    eff_H = [eff_AH, eff_BH]
    eff_A = [eff_AA, eff_BA]
    eff_D = [eff_AD, eff_BD]


    Teams_to_predict = [team_A, team_B]
    Teams_Mateches = [0, 0]
    for j in range(2):
        Matches = []
        for i in range(football_data.last_valid_index() + 1):
            if football_data["HomeTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "H":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "D":
                    Matches.append(football_data["FTR"][i])
            elif football_data["AwayTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "A":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "D":
                    Matches.append(football_data["FTR"][i])

        # Matches.reverse()
        # del Matches[5:]
        # Matches.reverse()
        Teams_Mateches[j] = Matches
    print(Teams_Mateches)

    # Create the model with edges specified as tuples (parent, child)
    edges = []
    for i in range(2):
        edges.append(('Team' + str(i), 'Efficiency' + str(i)))
        edges.append(('Team' + str(i), 'Run' + str(i)))
        edges.append(('Team' + str(i), 'Venue' + str(i)))

    football_model = BayesianModel(edges)

    # Create tabular CPDs, values has to be 2-D array
    cpd_run = []
    cpd_efficiency = []
    cpd_venue = []
    cpd_team = []

    for i in range(2):
        cpd_run.append(TabularCPD('Run' + str(i), 2, [[0.95, 0.95, 0.6], [0.05, 0.05, 0.4]], evidence=['Team' + str(i)],
                                  evidence_card=[3]))
        cpd_efficiency.append(
            TabularCPD('Efficiency' + str(i), 2, [[eff_H[i], eff_A[i], eff_D[i]], [1-eff_H[i], 1-eff_A[i], 1-eff_D[i]]], evidence=['Team' + str(i)],
                       evidence_card=[3]))
        cpd_venue.append(TabularCPD('Venue' + str(i), 2, [[0.6, 0.4, 0.5], [0.4, 0.6, 0.5]], evidence=['Team' + str(i)],
                                    evidence_card=[3]))
        cpd_team.append(TabularCPD('Team' + str(i), 3, [[0.35], [0.35], [0.3]]))

    # Add CPDs to model
    football_model.add_cpds(*cpd_run, *cpd_efficiency, *cpd_venue, *cpd_team)

    print('Check model :', football_model.check_model())

    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)

    q0 = football_infer.query(['Team0'], evidence={'Efficiency0': 0, 'Run0': 1, 'Venue0': 0}, show_progress=False)
    print('P(Team0|E0, R0, V0) =\n', q0)
    home0 = q0.values[0]
    draw0 = q0.values[2]

    q1 = football_infer.query(['Team1'], evidence={'Efficiency1': 0, 'Run1': 0, 'Venue1': 1}, show_progress=False)
    print('P(Team1|E1, R1, V1) =\n', q1)
    away1 = q1.values[1]
    draw1 = q1.values[2]

    sub_draw = abs(draw0 - draw1)

    if sub_draw < 0.15 and draw0 > 0.4 and draw1 > 0.4:
        print("D")
    elif home0 > away1:
        print("H")
    elif away1 > home0:
        print("A")


if __name__ == '__main__':
    main()
