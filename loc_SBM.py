import numpy as np
import random
from stochastic_block_model import get_B_and_weight_vec
from sbm import SBM
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
import networkx as nx
import localgraphclustering as lgc


def run(K=100, N1=100, N2=100, alpha=6, M=0.005, lambda_nLasso = 1/25):

    # parameters for M=0.6
    M = 0.6
    K = 500
    alpha = 0.4
    lambda_nLasso = 1/50

    # parameters for M=0.3
    M = 0.3
    K = 1500
    alpha = 0.1  # 0.09
    lambda_nLasso = 1/100

    # parameters for M = 0.2
    M = 0.2
    K = 4000
    alpha = 0.025
    lambda_nLasso = 1/200

    # B, weight_vec = get_B_and_weight_vec(N1, N2, mu_in=2, mu_out=0.5, pin=0.2, pout=0.02)

    model = SBM(N1+N2, 2, [1 for i in range(N1)] + [0 for i in range(N2)], pin=0.2, pout=0.01)
    B = model.B

    E, N = B.shape
    weight_vec = np.ones(E)

    Gamma_vec = (1./(np.sum(abs(B), 0))).T  # \in [0, 1]
    Gamma = np.diag(Gamma_vec)

    Sigma = np.diag(np.full(E, 0.5))

    if np.linalg.norm(np.dot(Sigma**0.5, B).dot(Gamma**0.5), 2) > 1:
        print (np.linalg.norm(np.dot(Sigma**0.5, B).dot(Gamma**0.5), 2))
        raise Exception('norm is greater than 1')

    samplingset = random.choices([i for i in range(N1)], k=int(M*N1))

    seednodesindicator= np.zeros(N)
    seednodesindicator[samplingset] = 1
    noseednodeindicator = np.ones(N)
    noseednodeindicator[samplingset] = 0

    s = 0.0
    for item in range(len(B)):
        i = np.where(B[item] == -1)[0][0]
        j = np.where(B[item] == 1)[0][0]
        if i < N1 <= j:
            s += weight_vec[i]
        if i >= N1 > j:
            s += weight_vec[i]

    if lambda_nLasso * s >= alpha * N2 / 2:
        print (lambda_nLasso * s, alpha * N2 / 2)
        raise Exception('error')

    fac_alpha = 1./(Gamma_vec*alpha+1)  # \in [0, 1]

    hatx = np.zeros(N)
    newx = np.zeros(N)
    prevx = np.zeros(N)
    haty = np.array([x/(E-1) for x in range(0, E)])
    for iterk in range(K):
        tildex = 2 * hatx - prevx
        newy = haty + 1/2 * np.dot(B, tildex)  # chould be negative
        haty = newy / np.maximum(abs(newy) / (lambda_nLasso * weight_vec), np.ones(E))  # could be negative

        newx = hatx - Gamma_vec * np.dot(B.T, haty)  # could  be negative

        for dmy in range(len(samplingset)):
            idx_dmy = samplingset[dmy]
            newx[idx_dmy] = (newx[idx_dmy] + Gamma_vec[idx_dmy]) / (1 + Gamma_vec[idx_dmy])

        newx = seednodesindicator * newx + noseednodeindicator * (newx * fac_alpha)
        prevx = np.copy(hatx)
        hatx = newx  # could be negative

    if np.max(abs(newx-prevx)) > 1e-4:
        raise Exception('increase iterations')

    # kmeans = KMeans(n_clusters=2, random_state=0).fit(newx.reshape(len(newx), 1))
    # predicted_labels = kmeans.labels_
    predicted_labels = np.copy(newx)
    predicted_labels[predicted_labels < 0.5] = 0
    predicted_labels[predicted_labels >= 0.5] = 1
    true_labels = [1 for i in range(N1)] + [0 for i in range(N2)]
    acc = accuracy_score(true_labels, predicted_labels)
    return newx, acc, model, samplingset


def calculate_acc(clusterout, gr, N1, N2):
    xhat1 = np.zeros((len(list(gr.nodes)), 1))

    for nodei in clusterout:
        xhat1[nodei] = 1

    true_labels = [1 for i in range(N1)] + [0 for i in range(N2)]
    acc1 = accuracy_score(true_labels, xhat1)

    true_labels = [0 for i in range(N1)] + [1 for i in range(N2)]
    acc2 = accuracy_score(true_labels, xhat1)

    acc = max(acc1, acc2)
    return acc


def compare(N1=100, N2=100):
    newx, acc, model, seednodes = run(N1=N1, N2=N2)
    print ('our method accuracy is', acc)

    adjacency_matrix = model.block_matrix
    rows, cols = np.where(adjacency_matrix == 1)
    edges = zip(rows.tolist(), cols.tolist())
    gr = nx.Graph()
    gr.add_edges_from(edges)

    Glgc = lgc.GraphLocal.from_networkx(gr.to_undirected())

    acl = lgc.approximate_PageRank_weighted(Glgc, seednodes)
    approximate_PageRank_acc = calculate_acc(acl[0], gr, N1, N2)
    print ('approximate_PageRank_weighted accuracy is', approximate_PageRank_acc)

    acl = lgc.capacity_releasing_diffusion(Glgc, seednodes)
    capacity_releasing_acc = calculate_acc(acl[0], gr, N1, N2)
    print ('capacity_releasing_diffusion accuracy is', capacity_releasing_acc)

    Sacl, condacl = lgc.spectral_clustering(Glgc, seednodes, method="acl")  # one step
    Smqi, condmqi = lgc.flow_clustering(Glgc, Sacl, method="mqi")
    flow_acc = calculate_acc(Smqi, gr, N1, N2)
    print ('flow_clustering accuracy is', flow_acc)


