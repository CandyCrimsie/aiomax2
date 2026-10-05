# Architecture

The package is divided by responsibility rather than by endpoint count:

```text
src/aiomax2/
├── client/          pooled aiohttp transport, TLS, retries, rate limiting
├── types/           Pydantic models and MAX update parsing
├── dispatcher/      observers, routers, middleware, DI, dispatcher
├── filters/         base filter, Command, magic F, state filter
├── fsm/             states, context, strategies, storage
├── webhook/         transport-neutral handler and framework adapters
├── bot.py           typed low-level MAX API facade
├── enums.py         values defined by the MAX schema
└── exceptions.py    transport/API/framework errors
```

The processing pipeline is:

```text
raw JSON
  -> parse_update (discriminator-aware, unknown-update tolerant)
  -> bind Bot to shortcut-capable objects
  -> Dispatcher context + FSM context
  -> root update middleware/observer
  -> matching event observer on each Router
  -> outer middleware
  -> filters (may enrich context)
  -> inner middleware
  -> signature-based handler invocation
```

## Important boundaries

`AiohttpSession` owns transport concerns. `Bot` owns MAX endpoint semantics and
model conversion. The dispatcher never builds HTTP requests. Models may call a
bound `Bot` only through explicit shortcuts.

The `Update` parser uses an explicit mapping instead of relying solely on an
OpenAPI-generated discriminated union. This both fixes generator limitations
documented by MAX and preserves unknown future updates as generic objects.

The framework context is a mutable dictionary scoped to one update. Filters
and middleware may add values; handler invocation only passes named values
accepted by the callable. This gives aiogram-like dependency injection without
a service container or implicit global state.

## Delivery guarantees

Webhook secret comparison is constant-time. A successful HTTP response means
the update was parsed and dispatched. Applications that require durable or
exactly-once processing should acknowledge into their own queue before doing
business work; the framework itself does not claim such a guarantee.

The HTTP layer automatically retries rate-limit responses according to
`Retry-After`. Network and 5xx retries are restricted to idempotent methods by
default. Non-idempotent MAX operations are not replayed after ambiguous network
failures.

