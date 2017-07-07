import numpy as np

from generator import generate_responses_gt
from helpers.method_2 import classify_papers, generate_responses
from fusion_algorithms.algorithms_utils import input_adapter
from fusion_algorithms.em import expectation_maximization


def do_first_round(n_papers, criteria_num, papers_worker, J, lr, GT,
                   criteria_power, acc, criteria_difficulty, values_prob):
    # n workers
    N = (n_papers / papers_worker) * J

    power_cr_list = []
    acc_cr_list = []
    for cr in range(criteria_num):
        # generate responses
        GT_cr = [GT[p_id * criteria_num + cr] for p_id in range(n_papers)]
        responses_cr = generate_responses_gt(n_papers, [criteria_power[cr]], papers_worker,
                                             J, acc, [criteria_difficulty[cr]], GT_cr)
        # aggregate responses
        Psi = input_adapter(responses_cr)
        a, p = expectation_maximization(N, n_papers, Psi)

        # update values_prob, copmute cr_power, cr_accuracy
        p_out_list = []
        for e_id, e in enumerate(p):
            for e_v, e_p in e.iteritems():
                values_prob[e_id][e_v] = e_p
            p_out_list.append(values_prob[e_id][1])
        power_cr_list.append(np.mean(p_out_list))
        acc_cr_list.append(np.mean(a))

    classified_p, classified_p_ids, rest_p_ids = classify_papers(range(n_papers), criteria_num, values_prob, lr)
    return classified_p, classified_p_ids, rest_p_ids


def assign_criteria(papers_ids, criteria_num, values_prob):
    return [0 for _ in papers_ids]


def do_round(GT, lr, papers_ids, criteria_num, papers_worker, J,
             acc, criteria_difficulty, cr_assigned):
    # generate responses
    n = len(papers_ids)
    papers_ids_rest1 = papers_ids[:n - n % papers_worker]
    papers_ids_rest2 = papers_ids[n - n % papers_worker:]
    responses_rest1 = generate_responses(GT, papers_ids_rest1, criteria_num,
                                         papers_worker, acc, criteria_difficulty,
                                         cr_assigned)
    responses_rest2 = generate_responses(GT, papers_ids_rest2, criteria_num,
                                         papers_worker, acc, criteria_difficulty,
                                         cr_assigned)
    responses = responses_rest1 + responses_rest2
    pass



def get_loss_cost_smrun(criteria_num, n_papers, papers_worker, J, lr, Nt,
                        acc, criteria_power, criteria_difficulty, GT):
    # initialization
    values_prob = [[0., 0.] for _ in range(n_papers*criteria_num)]

    # Baseline round
    # 10% papers
    criteria_count = (Nt + papers_worker * criteria_num) * J * (n_papers / 10) / papers_worker
    first_round_res = do_first_round(n_papers/10, criteria_num, papers_worker, J, lr, GT,
                                     criteria_power, acc, criteria_difficulty, values_prob)
    classified_p, classified_p_ids, rest_p_ids = first_round_res

    # Do Multi rounds
    rest_p_ids = rest_p_ids + range(n_papers/10, n_papers)
    cr_assigned = assign_criteria(rest_p_ids, criteria_num, values_prob)
    do_round(GT, lr, rest_p_ids, criteria_num, papers_worker*criteria_num, J,
             acc, criteria_difficulty, cr_assigned)

