application(demo5, [ms1, ms2, ms3, ms4, ms5], [ep1, ep2, ep3, ep4, ep5]).

microservice(ms1, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms2, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms3, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms4, rr(0.1, 0.1, 0.1, 0.1), 1).
microservice(ms5, rr(0.1, 0.1, 0.1, 0.1), 1).

endpoint(ep1, [ms1]).
endpoint(ep2, [ms2]).
endpoint(ep3, [ms3]).
endpoint(ep4, [ms4]).
endpoint(ep5, [ms5]).

probability(ep1, 0.2).
probability(ep2, 0.2).
probability(ep3, 0.2).
probability(ep4, 0.2).
probability(ep5, 0.2).

functionalUnits(demo5, 10000).