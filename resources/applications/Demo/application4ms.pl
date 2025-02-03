application(demo4, [ms1, ms2, ms3, ms4], [ep1, ep2, ep3, ep4]).

microservice(ms1, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms2, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms3, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms4, rr(0.1, 0.1, 0.1, 0.1), 1).

endpoint(ep1, [ms1]).
endpoint(ep2, [ms2]).
endpoint(ep3, [ms3]).
endpoint(ep4, [ms4]).

probability(ep1, 0.25).
probability(ep2, 0.25).
probability(ep3, 0.25).
probability(ep4, 0.25).

functionalUnits(demo4, 10000).