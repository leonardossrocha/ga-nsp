import time
import random
import numpy as np
import os
from contextlib import redirect_stdout


# Funções de leitura das matrizes
#######################################################################
def ler_mat1(caminho_nsp):
    with open(caminho_nsp, 'r') as file:
        linha = file.readline().strip().split()
        NUM_ENF, NUM_D, NUM_T = map(int, linha)
    return NUM_ENF, NUM_D, NUM_T


def ler_mat2(caminho_nsp, start_line_mat2=0):
    mat2 = []
    with open(caminho_nsp, 'r') as file:
        for _ in range(start_line_mat2):
            next(file)
        for _ in range(7):
            linha = list(map(int, file.readline().strip().split()))
            mat2.append(linha)
    return mat2


def ler_mat3(caminho_nsp, start_line_mat3=0):
    mat3 = []
    with open(caminho_nsp, 'r') as file:
        for _ in range(start_line_mat3):
            next(file)
        for _ in range(25):
            linha = list(map(int, file.readline().strip().split()))
            mat3.append(linha)
    return mat3


def ler_mat_gen(caminho_gen):
    with open(caminho_gen, 'r') as file:
        mat1 = list(map(int, file.readline().strip().split()))
        file.readline()
        mat2 = list(map(int, file.readline().strip().split()))
        file.readline()
        mat3 = list(map(int, file.readline().strip().split()))
        file.readline()
        file.readline()
        mat4 = []
        for _ in range(4):
            linha = list(map(int, file.readline().strip().split()))
            mat4.append(linha)
    return mat1, mat2, mat3, mat4


def ler_arquivos(caminho_base_nsp, caminho_base_gen, num_arquivos_nsp, num_arquivos_gen):
    dados_nsp = []
    dados_gen = []
    for num in range(1, num_arquivos_nsp + 1):
        caminho_nsp = f"{caminho_base_nsp}/{num}.nsp"
        NUM_ENF, NUM_D, NUM_T = ler_mat1(caminho_nsp)
        matriz2 = ler_mat2(caminho_nsp, 2)
        matriz3 = ler_mat3(caminho_nsp, 10)
        dados_nsp.append((NUM_ENF, NUM_D, NUM_T, matriz2, matriz3))
    for num in range(1, num_arquivos_gen + 1):
        caminho_gen = f"{caminho_base_gen}/{num}.gen"
        mat1_gen, mat2_gen, mat3_gen, mat4_gen = ler_mat_gen(caminho_gen)
        dados_gen.append((mat1_gen, mat2_gen, mat3_gen, mat4_gen))
    return dados_nsp, dados_gen


caminho_base_nsp = 'NSPLib/N25'
caminho_base_gen = 'NSPLib/Cases'
num_arquivos_nsp = 100
num_arquivos_gen = 8

dados_nsp, dados_gen = ler_arquivos(caminho_base_nsp, caminho_base_gen, num_arquivos_nsp, num_arquivos_gen)

# Constantes para o algoritmo genético
NUM_ENFERMEIROS = dados_nsp[0][0]
NUM_DIAS = dados_nsp[0][1]
TURNOS = ["Manhã", "Tarde", "Noite", "Folga"]
POPULACAO_SIZE = 100
GERACOES = 100
TAXA_MUTACAO = 0.1


def avaliar_individuo(individuo, preferencias, matriz_turnos, mat_gen):
    fitness = 0
    minimo_dias, maximo_dias = mat_gen[2]
    minimo_consecutivas, maximo_consecutivas, minimo_turno, maximo_turno = mat_gen[3][0]
    for enfermeiro_idx, enfermeiro in enumerate(individuo):
        if enfermeiro_idx >= len(preferencias):
            continue
        num_dias_trabalhados = sum(1 for turno in enfermeiro if turno != "Folga")
        for i in range(1, NUM_DIAS):
            if i >= len(enfermeiro):
                continue
            if enfermeiro[i - 1] == "Tarde" and enfermeiro[i] == "Manhã":
                fitness -= 1
            if enfermeiro[i - 1] == "Noite" and enfermeiro[i] == "Manhã":
                fitness -= 1
            if enfermeiro[i - 1] == "Noite" and enfermeiro[i] == "Tarde":
                fitness -= 1
        if num_dias_trabalhados < minimo_dias:
            fitness -= (minimo_dias - num_dias_trabalhados)
        elif num_dias_trabalhados > maximo_dias:
            fitness -= (num_dias_trabalhados - maximo_dias)
        consecutivas = 1
        for i in range(1, NUM_DIAS):
            if i >= len(enfermeiro):
                continue
            if enfermeiro[i] == enfermeiro[i - 1] and enfermeiro[i] != "Folga":
                consecutivas += 1
            else:
                if consecutivas < minimo_consecutivas:
                    fitness -= (minimo_consecutivas - consecutivas)
                elif consecutivas > maximo_consecutivas:
                    fitness -= (consecutivas - maximo_consecutivas)
                consecutivas = 1
        for turno in TURNOS:
            if turno != "Folga":
                num_turno = enfermeiro.count(turno)
                if num_turno < minimo_turno:
                    fitness -= (minimo_turno - num_turno)
                elif num_turno > maximo_turno:
                    fitness -= (num_turno - maximo_turno)
        for i in range(NUM_DIAS):
            if enfermeiro_idx >= len(preferencias) or i >= len(preferencias[enfermeiro_idx]):
                continue
            turno = enfermeiro[i]
            preferencia = preferencias[enfermeiro_idx][i]
            fitness += preferencia
    return fitness


def criar_individuo():
    return [[random.choice(TURNOS) for _ in range(NUM_DIAS)] for _ in range(NUM_ENFERMEIROS)]


def criar_populacao():
    return [criar_individuo() for _ in range(POPULACAO_SIZE)]


def crossover(parent1, parent2):
    ponto_de_corte = random.randint(1, NUM_DIAS - 1)
    child1 = [parent1[i][:ponto_de_corte] + parent2[i][ponto_de_corte:] for i in range(NUM_ENFERMEIROS)]
    child2 = [parent2[i][:ponto_de_corte] + parent1[i][ponto_de_corte:] for i in range(NUM_ENFERMEIROS)]
    return child1, child2


def mutacao(individuo):
    for i in range(NUM_ENFERMEIROS):
        if random.random() < TAXA_MUTACAO:
            dia = random.randint(0, NUM_DIAS - 1)
            individuo[i][dia] = random.choice(TURNOS)
    return individuo


def algoritmo_genetico(preferencias, matriz_turnos, mat_gen):
    populacao = criar_populacao()
    inicio = time.time()

    for geracao in range(GERACOES):
        print(f"Geração {geracao + 1}")
        populacao = sorted(populacao, key=lambda ind: avaliar_individuo(ind, preferencias, matriz_turnos, mat_gen),
                           reverse=True)
        nova_populacao = populacao[:POPULACAO_SIZE // 2]
        while len(nova_populacao) < POPULACAO_SIZE:
            parent1, parent2 = random.sample(populacao[:POPULACAO_SIZE // 2], 2)
            child1, child2 = crossover(parent1, parent2)
            nova_populacao.extend([mutacao(child1), mutacao(child2)])
        populacao = nova_populacao

        melhores_individuos = sorted(populacao,
                                     key=lambda ind: avaliar_individuo(ind, preferencias, matriz_turnos, mat_gen),
                                     reverse=True)[:POPULACAO_SIZE // 2]
        populacao[-len(melhores_individuos):] = melhores_individuos

        for i, individuo in enumerate(populacao):
            print(
                f"Indivíduo {i + 1}: {individuo}, Fitness: {avaliar_individuo(individuo, preferencias, matriz_turnos, mat_gen)}")
        print("\n")

    fim = time.time()
    tempo_total = fim - inicio
    print(f"Tempo total de processamento: {tempo_total:.2f} segundos")

    melhor_individuo = max(populacao, key=lambda ind: avaliar_individuo(ind, preferencias, matriz_turnos, mat_gen))
    return melhor_individuo, avaliar_individuo(melhor_individuo, preferencias, matriz_turnos, mat_gen), tempo_total


with open('resultado.txt', 'w') as f:
    with redirect_stdout(f):
        for idx_nsp, (NUM_ENF, NUM_D, NUM_T, matriz2, matriz3) in enumerate(dados_nsp):
            print(f"\nExecutando algoritmo genético para o arquivo NSP {idx_nsp + 1}")
            preferencias = matriz3
            matriz_turnos = matriz2
            mat_gen = dados_gen[idx_nsp % len(dados_gen)]
            melhor_individuo, melhor_fitness, tempo_total = algoritmo_genetico(preferencias, matriz_turnos, mat_gen)
            minutos, segundos = divmod(tempo_total, 60)
            print("Melhor indivíduo:", melhor_individuo)
            print("Melhor fitness:", melhor_fitness)
            print(f"Tempo total de processamento: {int(minutos)} minutos e {segundos:.2f} segundos")
