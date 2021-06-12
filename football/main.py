#!/usr/bin/env python3
import pandas as pd
from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


def main():
    # pd.options.mode.chained_assignment = None

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

    # counting team's goals
    Goals = []
    temp_sum = 0
    for j in range(team_list.last_valid_index() + 1):
        goals_home = 0
        goals_away = 0
        loss_home = 0
        loss_away = 0
        print(Teams[j])
        for i in range(football_data.last_valid_index() + 1):
            if football_data["HomeTeam"][i] == Teams[j]:
                goals_home += (football_data["FTHG"][i])
                loss_home += (football_data["FTAG"][i])
            elif football_data["AwayTeam"][i] == Teams[j]:
                goals_away += (football_data["FTAG"][i])
                loss_away += (football_data["FTHG"][i])
        suma = goals_away + goals_home
        temp_sum += suma
        print('Goals: H:', goals_home, ' A:', goals_away)
        print('Loss: H:', loss_home, ' A:', loss_away)

    print(football_data)

    # # Create the model with edges specified as tuples (parent, child)
    # football_model = BayesianModel([])
    #
    # # Create tabular CPDs, values has to be 2-D array
    # cpd = TabularCPD()
    #
    # # Add CPDs to model
    # football_model.add_cpds(cpd)
    #
    # print('Check model :', football_model.check_model())
    #
    # print('Independencies:\n', football_model.get_independencies())
    #
    # # Initialize inference algorithm
    # football_infer = VariableElimination(football_model)


if __name__ == '__main__':
    main()
