"""Facet bounded context (v3.3).

`playbook`  parses a facet body into directives and a Playbook.
`catalog`   is the one seam that loads, caches, routes, renders and lints facets.

This package __init__ imports nothing: `core.facet_contract` imports
`core.facets.playbook` while parsing, and an eager import of `catalog` here
would close that cycle.
"""
