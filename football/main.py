#!/usr/bin/env python3

from pgmpy.models import BayesianModel
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


def main():
    # Create the model with edges specified as tuples (parent, child)
    football_model = BayesianModel([])

    # Create tabular CPDs, values has to be 2-D array
    cpd = TabularCPD()

    # Add CPDs to model
    football_model.add_cpds(cpd)

    print('Check model :', football_model.check_model())

    print('Independencies:\n', football_model.get_independencies())

    # Initialize inference algorithm
    football_infer = VariableElimination(football_model)


if __name__ == '__main__':
    main()
