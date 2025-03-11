% Load utility predicates.
:- ['utils.pl'].

timedPlacement(Mode, App, P, SCI, N, Time) :-
    statistics(cputime, TStart),
    placement(Mode, App, P, SCI, N),
    statistics(cputime, TEnd),
    Time is TEnd - TStart.

placement(greenonly, App, P, SCI, NumberOfNodes) :- placement(quick, 1, App, P, SCI, NumberOfNodes).
placement(capacityonly, App, P, SCI, NumberOfNodes) :- placement(quick, 2, App, P, SCI, NumberOfNodes).
placement(linearcombination, App, P, SCI, NumberOfNodes) :- placement(quick, 3, App, P, SCI, NumberOfNodes).
placement(quick, NSort, App, P, SCI, NumberOfNodes) :-
    scoredNodes(Nodes, NSort),
    application(App, _, EPs),
    scoredMicroservices(Microservices),
    functionalUnits(App, R),
    eligiblePlacement(Microservices, Nodes, P), 
    involvedNodes(P, NumberOfNodes),
    sci(EPs, R, P, SCI).
placement(base, App, P, SCI, NumberOfNodes) :-
    application(App, Ms, EPs),
    functionalUnits(App, R),
    eligiblePlacement(Ms, P), 
    involvedNodes(P, NumberOfNodes),
    sci(EPs, R, P, SCI).
placement(tempBase, App, P, SCI, NumberOfNodes) :-
    application(App, _, EPs),
    functionalUnits(App, R),
    involvedNodes(P, NumberOfNodes),
    sci(EPs, R, P, SCI).
placement(exhaustive, App, BestP, BestSCI, BestNumberOfNodes) :-
    findall(p(SCI, N, P), placement(base, App, P, SCI, N), [P|Placements]),
    findMinP(Placements, P, p(BestSCI,BestNumberOfNodes,BestP)).

findMinP([p(SCI,N,P)|Placement], p(OldMinSCI,_,_), p(NewSCI,NewN,NewP)) :-
    SCI < OldMinSCI,
    findMinP(Placement, p(SCI,N,P), p(NewSCI, NewN, NewP)).
findMinP([p(SCI,_,_)|Placement], p(OldMinSCI, OldN, OldP), p(NewSCI, NewN, NewP)) :-
    SCI >= OldMinSCI,
    findMinP(Placement, p(OldMinSCI, OldN, OldP), p(NewSCI, NewN, NewP)).
findMinP([], P, P).

scoredNodes(Nodes, NSort) :-
    retractall(cs(_,_)), retractall(rs(_,_)), retractall(ws(_,_)),
    carbonRankingFactors(), resourceRankingFactors(node),
    findall(candidate(CS,RS,WS,N), scores(N,CS,RS,WS), TmpNodes), 
    sort(NSort,@=<,TmpNodes,SNodes),
    findall(N, member(candidate(_,_,_,N), SNodes), Nodes),
    cleanUp().

scoredMicroservices(LstMs) :-
    retractall(rs(_,_)), resourceRankingFactors(microservice),
    findall(ms(RS,M), scores(M,RS), TmpMs), 
    sort(0,@=<,TmpMs,SMs),
    findall(M, member(ms(_,M), SMs), LstMs),
    cleanUp().

resourceScore(E, CPU, RAM, BWIn, BWOut, RS) :-
    maxResources(MaxCPU,MaxRAM,MaxBWIn,MaxBWOut),
    minResources(MinCPU,MinRAM,MinBWIn,MinBWOut),
    safeROp(0.25, CPU, MaxCPU, MinCPU, P1),
    safeROp(0.25, RAM, MaxRAM, MinRAM, P2),
    safeROp(0.25, BWIn, MaxBWIn, MinBWIn, P3),
    safeROp(0.25, BWOut, MaxBWOut, MinBWOut, P4),
    RS is P1 + P2 + P3 + P4, 
    assert(rs(E,RS)).

carbonScore(N,CS) :- 
    node(N,_,_,_,_,_),
    of(N,OF), minOF(MinOF), maxOF(MaxOF),
    safeCOp(0.5, OF, MaxOF, MinOF, P1),
    mf(N,MF), minMF(MinMF), maxMF(MaxMF),
    safeCOp(0.5, MF, MaxMF, MinMF, P2),
    CS is P1 + P2, assert(cs(N,CS)).

carbonRankingFactors() :-
    findall(OF, nodeOF(N,OF), OFs), max_list(OFs, MaxOF), min_list(OFs,MinOF),
    assert(maxOF(MaxOF)), assert(minOF(MinOF)),
    findall(MF, nodeMF(N,MF), MFs), max_list(MFs,MaxMF), min_list(MFs,MinMF),
    assert(maxMF(MaxMF)), assert(minMF(MinMF)).

nodeOF(N,OF) :- node(N,_,PowerPerCPU,_,_,PUE), carbon_intensity(N,I), OF is PUE * I * PowerPerCPU, assert(of(N,OF)).
nodeMF(N,MF) :- node(N,_,_,EL,TE,_), MF is TE/EL, assert(mf(N,MF)).

scores(Ms,RS) :- resourceScore(microservice,Ms,RS).
scores(N,CS,RS,WS) :- carbonScore(N,CS), resourceScore(node,N,RS), weightedScore(N,CS,RS,WS).

resourceScore(microservice,Ms,RS) :- microservice(Ms,rr(CPU, RAM, BWIn, BWOut),_), resourceScore(Ms, CPU, RAM, BWIn, BWOut, RS).
resourceScore(node,N,RS) :- node(N,tor(CPU, RAM, BWIn, BWOut),_,_,_,_), resourceScore(N, CPU, RAM, BWIn, BWOut, RS).

weightedScore(N,CS,RS,WS) :- 
    node(N,_,_,_,_,_),
    WS is (0.5 * CS) + (0.5 * RS), 
    assert(ws(N,WS)).

eligiblePlacement(LstMs, LstN, P) :- eligiblePlacement(LstMs, LstN, [], P).
eligiblePlacement(LstMs, P) :- eligible(LstMs, [], P).
eligiblePlacement([M|LstMs], LstN, P, NewP) :-
    microservice(M, RR, _),
    member(N,LstN), placementNode(N, P, RR),
    eligiblePlacement(LstMs, LstN, [on(M,N)|P], NewP).
eligiblePlacement([], _, P, P).

eligible([Ms|LstMs], P, NewP) :-
    microservice(Ms, RR, _),
    placementNode(N, P, RR),
    eligible(LstMs, [on(Ms,N)|P], NewP).
eligible([], P, P).

placementNode(N, P, rr(CPUReq, RAMReq, BWinReq, BWoutReq)) :-
    node(N, tor(CPU, RAM, BWin, BWout), _, _, _, _),
    hardwareUsedAtNode(N, P, rr(UCPU, URAM, UBWin, UBWout)),
    CPU >= UCPU + CPUReq, 
    RAM >= URAM + RAMReq, 
    BWin >= UBWin + BWinReq, 
    BWout >= UBWout + BWoutReq.

involvedNodes(P, InvolvedNodes) :-
    findall(N, distinct(node(N,_), member(on(_,N),P)), Nodes), 
    length(Nodes, InvolvedNodes).

hardwareUsedAtNode(N, P, rr(UCPU, URAM, UBWin, UBWout)) :-
    findall(rr(CPU,RAM,BWin,BWout), (member(on(Ms,N),P), microservice(Ms,rr(CPU,RAM,BWin,BWout),_)), RRs),
    sumHWReqs(RRs, rr(UCPU, URAM, UBWin, UBWout)).

sumHWReqs([rr(CPU,RAM,BWin,BWout) | RRs], rr(TCPU, TRAM, TBWin, TBWout)) :-
    sumHWReqs(RRs, rr(AccCPU, AccRAM, AccBWin, AccBWout)),
    TCPU is AccCPU + CPU,
    TRAM is AccRAM + RAM,
    TBWin is AccBWin + BWin,
    TBWout is AccBWout + BWout.
sumHWReqs([], rr(0,0,0,0)).

sci(EPs, R, P, SCI) :- sci(EPs,R,P,0,SCI).
sci([EP|EPs], R, P, OldSCI, NewSCI) :-
    endpointSCI(EP,R,P,EPSCI),
    TmpSCI is OldSCI + EPSCI,
    sci(EPs,R,P,TmpSCI,NewSCI).
sci([],_,_,SCI,SCI).

endpointSCI(EP, R, P, SCI) :-
    endpoint(EP, EPMs),
    findall(on(Ms,N), (member(Ms, EPMs), member(on(Ms, N), P)), FilteredP),
    probability(EP, Prob),
    carbonEmissions(FilteredP, C),
    SCI is (C / R) * Prob.

carbonEmissions([on(Ms,N)|P], C) :-
    carbonEmissions(P, AccC),
    operationalCarbon(N, Ms, O),
    embodiedCarbon(N, Ms, E),
    C is AccC + O + E.
carbonEmissions([], 0).

operationalEnergy(N, Ms, E) :-
    node(N, _, PowerPerCPU, _, _, PUE),
    microservice(Ms, _, TiR),
    E is PUE * (TiR * 365 * 24) * PowerPerCPU.

operationalCarbon(N, Ms, O) :-
    carbon_intensity(N, I),
    operationalEnergy(N, Ms, E),
    O is E * I.

embodiedCarbon(N, Ms, M) :-
    node(N, tor(CPU,_,_,_), _, EL, TE, _),
    microservice(Ms, rr(CPUReq,_,_,_), TiR),
    TS is TiR / EL,
    RS is CPUReq / CPU,
    M is TE * TS * RS.