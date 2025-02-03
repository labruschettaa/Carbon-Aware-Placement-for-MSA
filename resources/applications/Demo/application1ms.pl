application(demo1, [ms1], [ep1]).

microservice(ms1, rr(0.1, 0.1, 0.1, 0.1), 1).

endpoint(ep1, [ms1]).

probability(ep1, 1).
  
functionalUnits(demo1, 10000).