application(onlineBoutiqueSeven, [frontend, currency, recommendation, shipping, ad, cart, product_catalog], [home, product, addToCart, viewCart, emptyCart]).

microservice(frontend, rr(0.1, 0.128, 0.01, 0.01), 1).
microservice(shipping, rr(1, 1.0, 0.2, 0.2), 1).
microservice(product_catalog, rr(0.5, 1.3, 0.3, 0.3), 1).
microservice(recommendation, rr(0.5, 1.2, 0.3, 0.3), 1).
microservice(cart, rr(0.2, 0.8, 0.2, 0.2), 1).
microservice(ad, rr(0.2, 0.6, 0.2, 0.2), 1).
microservice(currency, rr(0.2, 0.3, 0.05, 0.05), 1).

endpoint(emptyCart, [frontend, cart]).
endpoint(addToCart, [frontend, product_catalog, cart]).
endpoint(home, [frontend, currency, product_catalog, cart]).
endpoint(product, [frontend, product_catalog, currency, ad, cart, recommendation]).
endpoint(viewCart, [frontend, cart, currency, product_catalog, shipping, recommendation]).

probability(home, 0.25).
probability(product, 0.4).
probability(addToCart, 0.1).
probability(emptyCart, 0.05).
probability(viewCart, 0.15).

functionalUnits(onlineBoutiqueSeven, 10000).