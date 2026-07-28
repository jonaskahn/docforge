# Low-level architecture writing craft

Organize by subsystem responsibility, not directory traversal. For each
subsystem, explain inputs, state transitions, outputs, failure containment, and
adjacent dependencies in that order. Use a sequence or data-flow diagram when
prose would force the reader to reconstruct a multi-step interaction. Close
each section with the stable file/module paths that orient implementation work.
