
#!/usr/bin/env python
# coding=utf-8

"""
The class SSRacos represents SSRacos algorithm. It's inherited from SRacos.


Author:
    Xionghui Chen
"""

import time
import numpy
from zoopt.solution import Solution
from zoopt.algos.racos.racos_classification import RacosClassification
from zoopt.algos.racos.racos_common import RacosCommon
from zoopt.utils.zoo_global import gl
from zoopt.utils.tool_function import ToolFunction
from zoopt.algos.racos.sracos import SRacos


class SSRacos(SRacos):

    def __init__(self):
        SRacos.__init__(self)
        return

    # SRacos's optimization function
    # Default strategy is WR(worst replace)
    # Default uncertain_bits is 1, but actually ub will be set either by user
    # or by RacosOptimization automatically.
    def opt(self, objective, parameter, strategy='WR', ub=1):
        self.clear()
        self.set_objective(objective)
        self.set_parameters(parameter)
        self.init_attribute()
        self.i = 0
        iteration_num = self._parameter.get_budget() - self._parameter.get_train_size()
        iteration_num = iteration_num
        time_log1 = time.time()
        max_distinct_repeat_times = 100
        current_not_distinct_times = 0
        last_best = None
        max_stay_function = parameter.get_max_stay_function()
        precision_function = parameter.get_precision_function()
        max_stay_times = max_stay_function(0)
        non_update_allowed = parameter.get_non_update_allowed()
        # baselines = parameter.get_baselines()
        # non_update_baselines_allowed = parameter.get_non_update_baseline_allowed()
        non_update_times = 0
        current_stay_times = 0
        non_update_baselines_times = 0
        dont_early_stop =False
        while self.i < iteration_num:
            if gl.rand.random() < self._parameter.get_probability():
                classifier = RacosClassification(
                    self._objective.get_dim(), self.get_real_positive_solution_list(), self._negative_data, ub)
                classifier.mixed_classification()
                solution, distinct_flag = self.distinct_sample_classifier(
                    classifier, True, self._parameter.get_train_size())
            else:
                solution, distinct_flag = self.distinct_sample(
                    self._objective.get_dim())
            # panic stop
            if solution is None:
                ToolFunction.log(" [break loop] solution is None")
                return self.get_best_solution()
            if distinct_flag is False:
                current_not_distinct_times += 1
                if current_not_distinct_times >= max_distinct_repeat_times:
                    ToolFunction.log(
                        "[break loop] distinct_flag is false too much times")
                    return self.get_best_solution()
                else:
                    continue
            # evaluate the solution
            objective.eval(solution)
            # suppression
            if self._is_worest(solution):
                non_update_times += 1
                if non_update_times >= non_update_allowed:
                    self._positive_data_re_sample()
                    self.update_possible_solution()
                    self._positive_data = self.sort_solution_list(
                        self._positive_data)
                    non_update_times = 0
                    best_solution = self.get_best_solution(for_test=True)
                    # if best_solution stay longer than max_stay_times, break
                    if last_best is not None and last_best - best_solution.get_resample_value() < parameter.get_max_stay_precision():
                        current_stay_times += 1

                        ToolFunction.log("[max stay test] last_best %s, current best %s, stay_times %s, max_stay_times %s, precision %s. iteration_num %s. i %s" % (
                            last_best, best_solution.get_resample_value(), current_stay_times, max_stay_times, gl.precision, iteration_num, self.i))
                        if current_stay_times >= max_stay_times:
                            ToolFunction.log(
                                "[max stay test][break loop] because stay longer than max_stay_times, break loop")
                            return self.get_best_solution()
                    else:
                        current_stay_times = 0
                        ToolFunction.log("[last best updated] last_best %s, current best %s, stay_times %s, max_stay_times %s, precision %s. iteration_num %s. i %s" % (
                            last_best, best_solution.get_resample_value(), current_stay_times, max_stay_times, gl.precision, iteration_num, self.i))

                    last_best = best_solution.get_resample_value()
                    max_stay_times = max_stay_function(last_best)
                    precision = precision_function(last_best)
                    gl.set_precision(precision)
                    self._parameter.set_precision(precision)
            else:
                non_update_times = 0
            bad_ele = self.replace(self._positive_data, solution, 'pos')
            self.replace(self._negative_data, bad_ele, 'neg', strategy)
            self._best_solution = self._positive_data[0]

            if self.i == 4:
                time_log2 = time.time()
                expected_time = (self._parameter.get_budget(
                ) - self._parameter.get_train_size()) * (time_log2 - time_log1) / 5
                if self._parameter.get_time_budget() is not None:
                    expected_time = min(
                        expected_time, self._parameter.get_time_budget())
                if expected_time > 5:
                    m, s = divmod(expected_time, 60)
                    h, m = divmod(m, 60)
                    ToolFunction.log(
                        'expected remaining running time: %02d:%02d:%02d' % (h, m, s))
            # time budget check
            if self._parameter.get_time_budget() is not None:
                if (time.time() - time_log1) >= self._parameter.get_time_budget():
                    ToolFunction.log('time_budget runs out')
                    return self.get_best_solution()
            # early stop
            if self._parameter.early_stop is not None and not dont_early_stop:
                if solution.get_value() < self._objective.return_before * 0.9:
                    dont_early_stop = True
                elif self.i > self._parameter.early_stop:
                    ToolFunction.log(
                        '[break loop] early stop for too low value.')
                    return self._positive_data[0]
                ToolFunction.log('[early stop warning ]: current iter %s , target %s ' % (self.i, self._parameter.early_stop))

            # terminal_value check
            if self._parameter.get_terminal_value() is not None:
                solution = self.get_best_solution(for_test=True)
                if solution is not None and solution.get_resample_value() <= self._parameter.get_terminal_value():
                    ToolFunction.log('terminal function value reached')
                    return self.get_best_solution()
            self.i += 1
        return self.get_best_solution()

    def update_possible_solution(self):
        for solution in self._positive_data:
            ToolFunction.log(" positive sollution list %s" % solution.get_value())
        for solution in self._positive_data:
            if solution.is_in_possible_solution:
                continue
            else:
                solution.is_in_possible_solution = True
                new_solution = solution.deep_copy()
                self._possible_solution_list.append(new_solution)

        for solution in self._possible_solution_list:
            ToolFunction.log(" best possible sollution list %s" %
                             solution.get_resample_value())

    def get_best_solution(self, for_test=False):
        if not for_test:
            # update solution in positive data
            self._positive_data_re_sample()
            self.update_possible_solution()
        # sort
        sort_solution = self.sort_solution_list(
            self._possible_solution_list, key=lambda x: x.get_resample_value())
        if sort_solution == []:
            return None
        else:
            if not for_test:
                sort_solution[0].set_value(
                    sort_solution[0].get_resample_value())
                return sort_solution[0]
            else:
                return sort_solution[0]

    def get_real_positive_solution_list(self):
        if len(self._possible_solution_list) < 1:  # self._parameter.get_positive_size():
            return self._positive_data
        else:
            solutions = self.sort_solution_list(
                self._possible_solution_list, key=lambda x: x.get_resample_value())
            # positive_solution = [solutions[0]]# self._parameter.get_positive_size()]
            # positive_solution.append(self._positive_data[0])
            solutions = self.sort_solution_list(
                self._possible_solution_list, key=lambda x: x.get_resample_value())
            half_size = int(self._parameter.get_positive_size()/2)
            positive_solution = self._positive_data[0:half_size]
            insert_number = 0
            for item in solutions:
                if item not in positive_solution:
                    positive_solution.append(item)
                    insert_number += 1
                    if insert_number >= half_size:
                        break
            return positive_solution

    def sort_solution_list(self, solution_list, key=lambda x: x.get_value()):
        return sorted(solution_list, key=key)
    # Find first element larger than x

    def binary_search(self, iset, x, begin, end):
        x_value = x.get_value()
        if x_value <= iset[begin].get_value():
            return begin
        if x_value >= iset[end].get_value():
            return end + 1
        if end == begin + 1:
            return end
        mid = (begin + end) // 2
        if x_value <= iset[mid].get_value():
            return self.binary_search(iset, x, begin, mid)
        else:
            return self.binary_search(iset, x, mid, end)

    def _positive_data_re_sample(self):
        for solution in self._positive_data:
            ToolFunction.log(" [before re sample]: positive sollution list %s" %
                             solution.get_value())
        for data in self._positive_data:
            self._objective.resample(
                data, self.get_parameters().get_resample_times())
            self._objective.record_distance(data.get_x())

    def _is_worest(self, solution):
        return self._positive_data[-1].get_value() <= solution.get_value()
