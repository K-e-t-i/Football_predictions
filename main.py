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
    print(Teams_Matches)

    # ------------------------------------------------------------------

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
                                       values=[[0.7, 0.3], [0.3, 0.7]],
                                       evidence=['Eff_0' + str(i)],
                                       evidence_card=[2]))

        cpd_eff_curr.append(TabularCPD(variable='Eff_curr' + str(i),
                                       variable_card=2,
                                       values=[[0.7, 0.3], [0.3, 0.7]],
                                       evidence=['Eff_prev' + str(i)],
                                       evidence_card=[2]))

        cpd_eff_predict.append(TabularCPD(variable='Eff_predict' + str(i),
                                          variable_card=2,
                                          values=[[0.7, 0.3], [0.3, 0.7]],
                                          evidence=['Eff_curr' + str(i)],
                                          evidence_card=[2]))

        cpd_result_prev.append(TabularCPD(variable='Result_prev' + str(i),
                                          variable_card=3,
                                          values=[[0.9, 0.1], [0.0, 0.1], [0.1, 0.8]],
                                          evidence=['Eff_prev' + str(i)],
                                          evidence_card=[2]))

        cpd_result_curr.append(TabularCPD(variable='Result_curr' + str(i),
                                          variable_card=3,
                                          values=[[0.9, 0.1], [0.0, 0.1], [0.1, 0.8]],
                                          evidence=['Eff_curr' + str(i)],
                                          evidence_card=[2]))

    # Add CPDs to model
    football_model.add_cpds(*cpd_e0, *cpd_eff_prev, *cpd_eff_curr, *cpd_eff_predict, *cpd_result_prev, *cpd_result_curr)

    print('Check model :', football_model.check_model())
    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)

    qH = football_infer.query(['Eff_predict0'], evidence={'Result_prev0': 1, 'Result_curr0': 2}, show_progress=False)
    print('P(Eff_predict0|Results=\n', qH)
    qA = football_infer.query(['Eff_predict1'], evidence={'Result_prev1': 1, 'Result_curr1': 1}, show_progress=False)
    print('P(Eff_predict1|Results=\n', qA)


if __name__ == '__main__':
    main()
