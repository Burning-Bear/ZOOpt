
from zoopt.solution import Solution
from zoopt.utils.zoo_global import pos_inf
import numpy as np
"""
The class Objective represents the objective function and its associated variables

Author:
    Yuren Liu
"""


class Objective:

    def __init__(self, func=None, dim=None, constraint=None, re_sample_func=None, balance_rate=1, tester=None,
                 origin_solution=None,
                 return_before=None, agent=None, update_q_func=None, re_eval_func=None,
                 copy_q_value_func=None, test_explore_actor_func=None):
        # Objective function defined by the user
        self.__func = func
        # Number of dimensions, dimension bounds are in the dim object
        self.__dim = dim
        # the function for inheriting solution attachment
        self.__inherit = self.default_inherit
        self.__post_inherit = self.default_post_inherit
        # the constraint function
        self.__constraint = constraint
        # the history of optimization
        self.__history = []
        self.__re_sample_func = re_sample_func
        self.__balance_rate = balance_rate
        self.tester = tester
        self.origin_solution = np.array(origin_solution)
        self.return_before = return_before
        self.agent = agent
        self.update_q_func = update_q_func
        self.re_eval_func = re_eval_func
        self.copy_q_value_func = copy_q_value_func
        self.test_explore_actor_func = test_explore_actor_func

    # Construct a solution from x
    def construct_solution(self, x, parent=None):
        new_solution = Solution()
        new_solution.set_x(x)
        new_solution.set_attach(self.__inherit(parent))
        # new_solution.set_value(self.__func(new_solution)) # evaluation should
        # be invoked explicitly
        return new_solution

    def record_distance(self, new_solution):

        distance = np.linalg.norm(np.array(new_solution) - self.origin_solution)
        ToolFunction.log("[distance] %s" % distance)
        self.tester.add_custom_record('distance', x=self.tester.time_step_holder.get_time(
        ), y=distance*200, x_name='time_step', y_name='distance')
    # evaluate the objective function of a solution

    def eval(self, solution):
        solution.set_value(self.__func(solution))
        self.__history.append(solution.get_value())
        solution.set_post_attach(self.__post_inherit())

    def resample(self, solution, v):
        if solution.get_resample_value() is None:
            solution.set_resample_value(self.__re_sample_func(solution, v))
            solution.set_value((1 - self.__balance_rate) * solution.get_value() +
                               self.__balance_rate * solution.get_resample_value())
            solution.set_post_attach(self.__post_inherit())

    def eval_constraint(self, solution):
        solution.set_value(
            [self.__func(solution), self.__constraint(solution)])
        self.__history.append(solution.get_value())
        solution.set_post_attach(self.__post_inherit())

    # set the optimization function
    def set_func(self, func):
        self.__func = func

    # get the optimization function
    def get_func(self):
        return self.__func

    # set the dimension object
    def set_dim(self, dim):
        self.__dim = dim

    # get the dimension object
    def get_dim(self):
        return self.__dim

    # set the attachment inheritance function
    def set_inherit_func(self, inherit_func):
        self.__inherit = inherit_func

    def set_post_inherit_func(self, inherit_func):
        self.__post_inherit = inherit_func

    def get_post_inherit_func(self):
        return self.__post_inherit

    # get the attachment inheritance function
    def get_inherit_func(self):
        return self.__inherit

    # set the constraint function
    def set_constraint(self, constraint):
        self.__constraint = constraint
        return

    # return the constraint function
    def get_constraint(self):
        return self.__constraint

    # get the optimization history
    def get_history(self):
        return self.__history

    # get the best-so-far history
    def get_history_bestsofar(self):
        history_bestsofar = []
        bestsofar = pos_inf
        for i in range(len(self.__history)):
            if self.__history[i] < bestsofar:
                bestsofar = self.__history[i]
            history_bestsofar.append(bestsofar)
        return history_bestsofar

    # clean the optimization history
    def clean_history(self):
        self.__history = []

    @staticmethod
    def default_inherit(parent=None):
        return None

    @staticmethod
    def default_post_inherit(parent=None):
        return None
