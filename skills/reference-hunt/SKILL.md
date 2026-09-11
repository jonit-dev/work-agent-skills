---
name: reference-hunt
description: >-
  Port the semantics of a reference implementation (a library, folder, or
  website module) when the user cannot describe what they want in words.
  Reads the reference's actual source, not screenshots or docs. Use when the
  user says "reference hunt", "照着这个实现", "find me a reference", points at
  code and says "like this", or struggles to articulate a behavior they can
  recognize.
---

# Reference Hunt

Sometimes the user cannot describe what they want in detail — they lack the
vocabulary, or describing it would take longer than showing it. The best
reference is source code.

## Workflow

1. **Get a pointer.** If the user already named a reference (a library, a
   vendored crate, a folder, a component on a website), start there. If not,
   propose 2-3 candidate references yourself — from the codebase, vendored
   dependencies, or well-known open-source implementations — and let the user
   pick. One short message, not an interview.
2. **Read the real implementation.** Read the reference's source code, not
   its README, docs, or a screenshot. For a website module, read the
   underlying markup and code — structure, state handling, how it is actually
   built. A different language than the target is fine; semantics transfer,
   syntax does not.
3. **Write down what you are taking.** Before implementing, give the user a
   short list: the semantics being ported (edge cases, state transitions,
   API shape, visual details), and what is deliberately *not* being ported.
   This is where the user's "I'd know it when I see it" gets checked cheaply.
4. **Reimplement, don't transplant.** Port the behavior into the target
   stack following the project's existing conventions and idioms. Cite the
   reference file paths in your summary so claims are checkable.

## Rules

- Never copy code verbatim from an external reference — port semantics,
  respect licenses, match the project's style.
- If the reference's behavior conflicts with something the user stated,
  surface the conflict instead of silently picking one.
- If the reference turns out to be a poor fit, say so and propose another —
  a bad reference is worse than none.
