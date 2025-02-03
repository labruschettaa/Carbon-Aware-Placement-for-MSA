application(demo3, [ms1, ms2, ms3], [ep1, ep2, ep3]).

microservice(ms1, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms2, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms3, rr(0.1, 0.1, 0.1, 0.1), 1).

endpoint(ep1, [ms1]).
endpoint(ep2, [ms2]).
endpoint(ep3, [ms3]).

probability(ep1, 0.33).
probability(ep2, 0.33).
probability(ep3, 0.34).

functionalUnits(demo3, 10000).