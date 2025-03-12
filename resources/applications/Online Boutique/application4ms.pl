application(onlineBoutiqueFour, [frontend, currency, cart, product_catalog], [home, addToCart, emptyCart]).

microservice(frontend, rr(0.1, 0.128, 0.01, 0.01), 1).
microservice(product_catalog, rr(0.5, 1.3, 0.3, 0.3), 1).
microservice(cart, rr(0.2, 0.8, 0.2, 0.2), 1).
microservice(currency, rr(0.2, 0.3, 0.05, 0.05), 1).

endpoint(emptyCart, [frontend, cart]).
endpoint(addToCart, [frontend, product_catalog, cart]).
endpoint(home, [frontend, currency, product_catalog, cart]).

probability(home, 0.25).
probability(addToCart, 0.1).
probability(emptyCart, 0.05).

functionalUnits(onlineBoutiqueFour, 10000).