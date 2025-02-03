application(onlineBoutiqueThree, [frontend, product_catalog, cart], [emptyCart, addToCart]).

microservice(frontend, rr(0.1, 0.128, 0.01, 0.01), 1).
microservice(product_catalog, rr(0.5, 1.3, 0.3, 0.3), 1).
microservice(cart, rr(0.2, 0.8, 0.2, 0.2), 1).

endpoint(emptyCart, [frontend, cart]).
endpoint(addToCart, [frontend, product_catalog, cart]).

probability(addToCart, 0.1).
probability(emptyCart, 0.05).

functionalUnits(onlineBoutiqueThree, 10000).