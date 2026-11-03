# Roadmap

The order of work on the edge protocol. A new version is announced with the KeyClerk release that speaks it, so an
edge ports once per version.

## Done
- 1.3.0: the address leaves the bundle, fetched by request.
- 1.2.x: an edge may wait for its next bundle; references cited where first named.
- 1.1.0: governed roles in the bundle.
- 1.0.0: the first public specification and conformance set.

## Next: 1.4.0, with KeyClerk 0.27.0
1. #10 Wire additions in one release: the records head the edge last saw in its report, the lease a session ran
   under, and removal confirmations per lease. All optional, so a 1.3 edge keeps working.

## Later
- Fields for a high-availability edge (how a node became active), with KeyClerk 0.28.0.
- Session constraints carried in the lease, with KeyClerk 0.30.0.
