# Security

Testule's public/private repository split is a source-exposure and distribution boundary, not an authorization boundary.

Report security-sensitive implementation findings through the private maintainer channel rather than publishing exploit details or protected fixtures in this repository.

## Public repository assumptions

Treat all material committed here as permanently public and mirrorable. Do not commit:

- credentials, tokens, signing keys, or secret values;
- private test corpora or protected verifier fixtures;
- canonical implementation source unless explicitly reclassified;
- host-specific private paths or operational configuration;
- confidential incident evidence.

Release artifacts are expected to be independently verifiable through checksums and provenance. A successful Testule test result never grants authority to mutate source, access secrets, use a network, or perform another consequential effect.

Historical Testule source that was previously public should be considered disclosed even after the canonical repository becomes private.
