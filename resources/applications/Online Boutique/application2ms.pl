application(onlineBoutiqueTwo, [frontend, cart], [emptyCart]).

microservice(cart, rr(0.2, 0.8, 0.2, 0.2), 1).
microservice(frontend, rr(0.1, 0.128, 0.01, 0.01), 1).

endpoint(emptyCart, [frontend, cart]).

probability(emptyCart, 0.05).
  
functionalUnits(onlineBoutiqueTwo, 10000).