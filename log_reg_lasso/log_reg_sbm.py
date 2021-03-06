import numpy as np
from stochastic_block_model import get_B_and_weight_vec
from log_reg_lasso.main import *


def threshold(val):
    return 1/(1+np.exp(val))


def run_reg_sbm(K, lambda_lasso, m, n, N1=150, N2=150, M=0.2):
    # TODO fix this
    m = 1
    M=1.0
    B, weight_vec = get_B_and_weight_vec([N1, N2], pout=0.001, mu_in=40, mu_out=10)
    E, N = B.shape

    X = []
    for i in range(N):
        # x, y = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, m))
        # d = np.sqrt(x * x + y * y)
        sigma, mu = 1.0, 0.0
        # g = np.exp(-((d - mu) ** 2 / (2.0 * sigma ** 2)))
        g = np.random.normal(mu, sigma, (m, n))
        X.append(g)
    X = np.array(X)

    W1 = np.random.random(n)
    W2 = np.random.normal(5, 2, n)
    print (W1, W2)

    Y = []
    for i in range(N):
        if i < N1:
            p = np.dot(X[i], W1)
        else:
            p = np.dot(X[i], W2)
        random_variable = np.random.uniform()
        Y.append(1 if random_variable > threshold(p)[0] else 0)
    Y = np.array(Y)

    return run(K, B, weight_vec, Y, X, lambda_lasso, method='norm', M=M)

# run_reg_sbm(K=1000, lambda_lasso=0.5, m=1, n=10,)