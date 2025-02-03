application(demo2, [ms1, ms2], [ep1, ep2]).

microservice(ms1, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms2, rr(0.1, 0.1, 0.1, 0.1), 1).

endpoint(ep1, [ms1]).
endpoint(ep2, [ms2]).

probability(ep1, 0.5).
probability(ep2, 0.5).

functionalUnits(demo2, 10000).