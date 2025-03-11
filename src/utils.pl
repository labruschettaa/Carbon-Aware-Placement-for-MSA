% Set up interpreter.
:- dynamic of/2, mf/2.
:- dynamic maxOF/1, minOF/1.
:- dynamic maxMF/1, minMF/1.
:- dynamic maxResources/4, minResources/4.
:- dynamic resourceScore/3.
:-set_prolog_flag(stack_limit, 16 000 000 000).
:-set_prolog_flag(last_call_optimisation, true).

:- multifile node/6, carbon_intensity/2.
:- dynamic node/6, carbon_intensity/2.
:- discontiguous node/6, carbon_intensity/2, placement/5.

cleanUp() :-
    retractall(of(_,_)), retractall(maxOF(_)), retractall(minOF(_)),
    retractall(mf(_,_)), retractall(maxMF(_)), retractall(minMF(_)), 
    retractall(maxResources(_,_,_,_)), retractall(minResources(_,_,_,_)).

safeCOp(F, E, MaxE, MinE, R) :-
    O is F*(E - MinE), D is MaxE - MinE,
    safeDiv(O, D, R).

safeROp(F, E, MaxE, MinE, R) :-
    O is F*(MaxE - E), D is MaxE - MinE, 
    safeDiv(O, D, R).

safeDiv(_, 0, 0).
safeDiv(_, 0.0, 0).
safeDiv(O, D, R) :- dif(D,0), dif(D,0.0), R is O / D.

resourceRankingFactors(microservice) :-
    findall(CPU,microservice(M,rr(CPU, RAM, BWIn, BWOut),_),CPUs), 
    max_list(CPUs,MaxCPU), min_list(CPUs,MinCPU),
    findall(RAM,microservice(M,rr(CPU, RAM, BWIn, BWOut),_),RAMs),
    max_list(RAMs,MaxRAM), min_list(RAMs,MinRAM),
    findall(BWIn,microservice(M,rr(CPU, RAM, BWIn, BWOut),_),BWIns),
    max_list(BWIns,MaxBWIn), min_list(BWIns,MinBWIn),
    findall(BWOut,microservice(M, rr(CPU, RAM, BWIn, BWOut),_),BWOuts), 
    max_list(BWOuts,MaxBWOut), min_list(BWOuts,MinBWOut),
    assert(maxResources(MaxCPU,MaxRAM,MaxBWIn,MaxBWOut)), assert(minResources(MinCPU,MinRAM,MinBWIn,MinBWOut)).

resourceRankingFactors(node) :-
    findall(CPU,node(N,tor(CPU, RAM, BWin, BWout),_,_,_,_),CPUs), 
    max_list(CPUs,MaxCPU), min_list(CPUs,MinCPU),
    findall(RAM,node(N,tor(CPU, RAM, BWin, BWout),_,_,_,_),RAMs),
    max_list(RAMs,MaxRAM), min_list(RAMs,MinRAM),
    findall(BWIn,node(N,tor(CPU, RAM, BWIn, BWout),_,_,_,_),BWIns),
    max_list(BWIns,MaxBWIn), min_list(BWIns,MinBWIn),
    findall(BWOut,node(N,tor(CPU, RAM, BWIn, BWOut),_,_,_,_),BWOuts), 
    max_list(BWOuts,MaxBWOut), min_list(BWOuts,MinBWOut),
    assert(maxResources(MaxCPU,MaxRAM,MaxBWIn,MaxBWOut)), assert(minResources(MinCPU,MinRAM,MinBWIn,MinBWOut)).