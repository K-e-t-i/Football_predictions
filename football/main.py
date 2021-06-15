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

    # Create ranking [('TeamName', Goals, Losses)] sorted by goals and losses
    Half_Sorted_Ranking = sorted(Ranking, key=itemgetter(4), reverse=False)
    Sorted_Ranking = sorted(Half_Sorted_Ranking, key=itemgetter(1), reverse=True)
    print(Sorted_Ranking)

    # ------------------------------------------------------------------

    team_A = "Fulham"
    team_B = "Liverpool"

    # create efficiency prob
    for i in range(len(Sorted_Ranking)):
        if Sorted_Ranking[i][0] == team_A:
            eff_AH = 0.9 - i * 0.02
            eff_AD = 0.4 + i * 0.01
            if Sorted_Ranking[i][2] > Sorted_Ranking[i][3]:
                eff_AH += 0.05

        elif Sorted_Ranking[i][0] == team_B:
            eff_BA = 0.9 - i * 0.02
            eff_BD = 0.6 + i * 0.01
            if Sorted_Ranking[i][2] < Sorted_Ranking[i][3]:
                eff_BA += 0.05

    eff = [eff_AH, eff_BA]
    eff_D = [eff_AD, eff_BD]

    # read results 4 last team matches
    Teams_to_predict = [team_A, team_B]
    Teams_Matches = [0, 0]
    for j in range(2):
        Matches = []
        for i in range(football_data.last_valid_index() + 1):
            if football_data["HomeTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "H":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "D":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "A":
                    Matches.append("L")
            elif football_data["AwayTeam"][i] == Teams_to_predict[j]:
                if football_data["FTR"][i] == "A":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "D":
                    Matches.append(football_data["FTR"][i])
                elif football_data["FTR"][i] == "H":
                    Matches.append("L")

        # 4 last matches: Last -> [0], One before last [1], Earlier [2], The Earliest [3]
        Matches.reverse()
        del Matches[4:]
        Teams_Matches[j] = Matches
    print(Teams_Matches)

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

        cpd_venue.append(TabularCPD('Venue' + str(i), 2, [[0.6, 0.4], [0.4, 0.6]], evidence=['Team' + str(i)],
                                    evidence_card=[2]))
        cpd_team.append(TabularCPD('Team' + str(i), 2, [[0.5], [0.5]]))

        for j in range(4):
            cpd_match.append(
                TabularCPD('Match' + str(i) + str(j), 3, [[0.7, 0.1, 0.3], [0.1, 0.6, 0.3], [0.2, 0.3, 0.4]], evidence=['Run' + str(i)],
                           evidence_card=[3]))

    # Add CPDs to model
    football_model.add_cpds(*cpd_run, *cpd_efficiency, *cpd_venue, *cpd_team, *cpd_match)

    print('Check model :', football_model.check_model())

    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)

    qA = football_infer.query(['Team0'], evidence={'Efficiency0': 0, 'Venue0': 0, 'Match00': 1, 'Match01': 1, 'Match02': 1, 'Match03': 2}, show_progress=False)
    print('P(Team0|E0, R0, V0) =\n', qA)
    winA = qA.values[0]
    drawA = qA.values[1]

    qB = football_infer.query(['Team1'], evidence={'Efficiency1': 0, 'Venue1': 1, 'Match10': 1, 'Match11': 0, 'Match12': 0, 'Match13': 2}, show_progress=False)
    print('P(Team1|E1, R1, V1) =\n', qB)
    winB = qB.values[0]
    drawB = qB.values[1]

    sub = abs(winA - winB)

    if drawA > 0.4 and drawB > 0.4 or sub < 0.2:
        print("D")
    elif winA > winB and sub > 0.2:
        print("H")
    elif winB > winA and sub > 0.2:
        print("A")


if __name__ == '__main__':
    main()
