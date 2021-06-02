from ortools.linear_solver import pywraplp
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="directory of file", type=str)
args = parser.parse_args()

start_time = time.time()

with open(args.file, 'r') as file:
    M, N, K = [int(x) for x in file.readline().split()]
    # Người
    p = [0]*(2*(M+N)+2*K+1)
    for i in range(1, M+1):
        p[i] = 1
    for i in range(M+N+1, M+N+1+M):
        p[i] = -1
    # Hàng
    q = [0]*(2*(M+N)+2*K+1)
    for index, X in enumerate(file.readline().split()):
        q[index+M+1] = int(X)
        q[index+2*M+N+1] = -int(X)
    # Max hàng
    Q = [0] * (K+1)
    for index, X in enumerate(file.readline().split()):
        Q[index + 1] = int(X)
    # Quãng đường
    d = [[int(i) for i in file.readline().split()] for j in range(2*(M+N)+1)]


def expand_start(d):
    n = 2*(M+N)
    n_expand = 2*(M+N)+2*K
    d_expand = np.zeros((n_expand+1, n_expand+1), dtype=int)
    for i in range(1, n+1):
        for j in range(1, n+1):
            d_expand[i][j] = d[i][j]
    for i in range(n+1, n_expand+1):
        for j in range(1, n+1):
            d_expand[i][j] = d[0][j]
    for i in range(1, n+1):
        for j in range(n+1, n_expand+1):
            d_expand[i][j] = d[i][0]
    return d_expand


d = expand_start(d)
print(M, N, K)
print(p)
print(q)
print(Q)
# for row in d:
#     print(row)

solver = pywraplp.Solver.CreateSolver('SCIP')
INF = 10000

B = {i for i in range(1, 2*(M+N)+2*K+1)}

B_2d, F1, F2, F3, F4, F5, F6 = set(), set(), set(), set(), set(), set(), set()
# Đi tại chỗ
for i in B:
    for j in B:
        B_2d.add((i, j))
# Điểm đón khách
for (i, j) in B_2d:
    if ((i in range(1, M+1))) and \
    (j in range(M+1, M+N+1) or j in range(2*M+N+1, 2*(M+N)+1) or j == i + M+N):
        F1.add((i, j))
# Điểm nhận hàng 
for (i, j) in B_2d:
    if ((i in range(M+1, M+N+1))) and (j in range(1, 2*(M+N)+1)):
        F2.add((i, j))
# Điểm trả khách
for (i, j) in B_2d:
    if (i in range(M+N+1, 2*M+N+1)) \
        and (j != i-N-M or (j in range(M+1, M+N+1)) \
        or (j in range(2*M+N+1, 2*(M+N)+1)) or (j in range(2*(M+N)+K+1, 2*(M+N)+2*K+1))):
        F3.add((i, j))
# Điểm trả hàng
for (i, j) in B_2d:
    if (i in range(2*M+N+1, 2*(M+N)+1)) and j!=i-M-N and (j not in range(2*(M+N)+1, 2*(M+N)+K+1)):
        F4.add((i, j))
# Điểm xuất phát
for (i, j) in B_2d:
    if (i in range(2*(M+N)+1, 2*(M+N)+K+1)) and ((j in range(1, (M+N)+1)) or j==i+K):
        F5.add((i, j))
# Đi tại chỗ
for i in B:
    F6.add((i, i))
A = F1.union(F2).union(F3).union(F4).union(F5)
A -= F6
print(A)

Ap = [[] for i in range(len(A))]
Am = [[] for i in range(len(A))]
for (i, j) in A:
    Ap[i].append(j)
    Am[j].append(i)

X, L, P, W, Z = {}, {}, {}, {}, {}
for k in range(1, K+1):
    for (i, j) in A:
        X[i, j] = solver.IntVar(0, 1, 'X({},{})'.format(i, j))
    for i in B:
        L[i] = solver.IntVar(0, INF, 'L({})'.format(i))
        P[i] = solver.IntVar(0, 1, 'P({})'.format(i))
        W[k, i] = solver.IntVar(0, Q[k], 'W({},{})'.format(k, i))
        Z[i] = solver.IntVar(1, K, 'Z({})'.format(i))

# leftVar = rightVar + param when X[i,j] = 1
def ConditionalX(leftVar, rightVar, param, i, j):
    c = solver.Constraint(-INF+int(param), INF)
    c.SetCoefficient(X[i, j], -INF)
    c.SetCoefficient(leftVar, 1)
    c.SetCoefficient(rightVar, -1)

    c = solver.Constraint(-INF-int(param), INF)
    c.SetCoefficient(X[i, j], -INF)
    c.SetCoefficient(leftVar, -1)
    c.SetCoefficient(rightVar, 1)

### Constraints

# Khởi tạo
for k in range(1, K+1):
    c = solver.Constraint(0, 0)
    c.SetCoefficient(L[2*(M+N)+k], 1)

    c = solver.Constraint(0, 0)
    c.SetCoefficient(P[2*(M+N)+k], 1)

    c = solver.Constraint(0, 0)
    c.SetCoefficient(W[k, 2*(M+N)+k], 1)

    c = solver.Constraint(k, k)
    c.SetCoefficient(Z[2*(M+N)+k], 1)

    c = solver.Constraint(k, k)
    c.SetCoefficient(Z[2*(M+N)+k+K], 1)

# Cân bằng luồng
for i in range(1, 2*(M+N)+1):
    c = solver.Constraint(1, 1)
    for j in Ap[i]:
        c.SetCoefficient(X[i, j], 1)

    c = solver.Constraint(1, 1)
    for j in Am[i]:
        c.SetCoefficient(X[j, i], 1)

# Nhận và trả hàng cùng xe
for i in range(1, M+N+1):
    c = solver.Constraint(0, 0)
    c.SetCoefficient(Z[i], -1)
    c.SetCoefficient(Z[i+(M+N)], 1)

# Tồn tại đường đi
for k in range(1, K+1):
    for (i, j) in A:
        ConditionalX(W[k, j], W[k, i], q[j], i, j)

for (i, j) in A:
    ConditionalX(Z[j], Z[i], 0, i, j)
    ConditionalX(L[j], L[i], d[i][j], i, j)
    ConditionalX(P[j], P[i], p[j], i, j)

# Điều kiện điểm trả sau điểm đón
for i in range(1, M+N+1):
    c = solver.Constraint(int(d[i][i+(M+N)]), INF)
    c.SetCoefficient(L[i], -1)
    c.SetCoefficient(L[i+(M+N)], 1)

# Điều kiện tải trọng
for i in B:
        c = solver.Constraint(0, 1)
        c.SetCoefficient(P[i], 1)

for k in range(1, K+1):
    for i in B:
        c = solver.Constraint(0, Q[k])
        c.SetCoefficient(W[k, i], 1)

# Objective
obj = solver.Objective()
for k in range(1, K+1):
    for (i, j) in A:
        obj.SetCoefficient(X[i, j], int(d[i][j]))
obj.SetMinimization()

result_status = solver.Solve()
assert result_status == pywraplp.Solver.OPTIMAL

print('optimal objective value: %.2f' % solver.Objective().Value())

# print route
for k in range(1, K+1):
    print("Vehicle {}:".format(k))
    rs = [None] * (2*(M+N) + 2*K+1)
    for (i, j) in A:
        if X[i, j].solution_value() > 0 and Z[i].solution_value() == k:
            rs[i] = j
            print(i, j, P[j].solution_value(),
                  W[k, j].solution_value(), L[j].solution_value())
    start = 0
    for i in range(K+2*(M+N), 2*(M+N)-1, -1):
        if(rs[i] != None):
            start = i
            end = i+K
            break

    if(rs[start]):
        print('{} -> '.format(2*(M+N)+k), end="")
        cur_index = rs[start]
        while(rs[cur_index]):
            print('{} -> '.format(cur_index), end="")
            cur_index = rs[cur_index]
        print('{}'.format(2*(M+N)+k+K))
    else:
        print('{} -> {}'.format(2*(M+N)+k, 2*(M+N)+k+K))
print(time.time() - start_time)
