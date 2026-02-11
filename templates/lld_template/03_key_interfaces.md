# Key Interfaces


## Public Interfaces

- List each public method or API endpoint exposed by this component
- Specify input parameters, return types, and side effects
- Note which interfaces are synchronous vs. asynchronous


## Internal Interfaces

- List key internal abstractions (e.g., strategy interfaces, repository interfaces)
- Describe what each abstraction decouples and why
- Note which implementations are swappable


## Error Contracts

- Define the error types this component can return (validation, not found, internal)
- Specify how errors propagate to callers (exceptions, error codes, result types)
- Note retry semantics: which errors are retryable and which are terminal
