"""
Preamble and Cover Page configuration for CoReOS System Guide.
"""

def get_preamble():
    return r'''
#set document(title: "CoReOS — Complete System Understanding Guide", author: "CoReOS Research Team")
#set page(
  paper: "a4",
  margin: (top: 2.6cm, bottom: 2.4cm, left: 2.2cm, right: 2.2cm),
  header: context {
    if counter(page).get().first() > 2 [
      #grid(
        columns: (1fr, 1fr),
        align(left)[#text(size: 8.5pt, fill: rgb("#64748B"), font: "Helvetica Neue", weight: "medium")[CoReOS: Complete System Understanding Guide]],
        align(right)[#text(size: 8.5pt, fill: rgb("#0D9488"), font: "Helvetica Neue", weight: "bold")[Operational & Research Manual]]
      )
      #v(2pt)
      #line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
    ]
  },
  footer: context {
    if counter(page).get().first() > 1 [
      #line(length: 100%, stroke: 0.5pt + rgb("#E2E8F0"))
      #v(3pt)
      #grid(
        columns: (1fr, 1fr),
        align(left)[#text(size: 8pt, fill: rgb("#94A3B8"), font: "Helvetica Neue")[Multi-Agent AI Operating System • Conflict-Aware & Self-Healing]],
        align(right)[#text(size: 8.5pt, fill: rgb("#475569"), font: "Helvetica Neue", weight: "bold")[Page #counter(page).display("1")]]
      )
    ]
  }
)

#set text(font: ("Helvetica Neue", "Arial"), size: 10pt, fill: rgb("#1E293B"))
#set par(justify: true, leading: 0.65em)
#set heading(numbering: "1.1")

// Heading Styling
#show heading.where(level: 1): it => block(
  above: 20pt,
  below: 12pt,
  breakable: false,
  [
    #v(6pt)
    #rect(
      fill: rgb("#F1F5F9"),
      stroke: (left: 4pt + rgb("#0D9488")),
      inset: (x: 12pt, y: 8pt),
      radius: (right: 4pt),
      width: 100%
    )[
      #text(fill: rgb("#0F172A"), size: 16pt, weight: "bold")[#it.body]
    ]
    #v(2pt)
  ]
)

#show heading.where(level: 2): it => block(
  above: 14pt,
  below: 8pt,
  breakable: false,
  [
    #text(fill: rgb("#0369A1"), size: 12.5pt, weight: "bold")[#it.body]
    #v(2pt)
  ]
)

#show heading.where(level: 3): it => block(
  above: 10pt,
  below: 6pt,
  breakable: false,
  [
    #text(fill: rgb("#334155"), size: 10.5pt, weight: "bold")[#it.body]
  ]
)

// Callout Boxes
#let info-box(title, body) = block(
  fill: rgb("#F0F9FF"),
  stroke: (left: 3.5pt + rgb("#0284C7"), rest: 0.5pt + rgb("#BAE6FD")),
  inset: 10pt,
  radius: (right: 4pt),
  width: 100%,
  above: 8pt,
  below: 8pt,
  [
    #text(fill: rgb("#0369A1"), weight: "bold", size: 9.5pt)[#title] \
    #v(3pt)
    #text(fill: rgb("#0F172A"), size: 9pt)[#body]
  ]
)

#let warning-box(title, body) = block(
  fill: rgb("#FFFBEB"),
  stroke: (left: 3.5pt + rgb("#D97706"), rest: 0.5pt + rgb("#FDE68A")),
  inset: 10pt,
  radius: (right: 4pt),
  width: 100%,
  above: 8pt,
  below: 8pt,
  [
    #text(fill: rgb("#B45309"), weight: "bold", size: 9.5pt)[#title] \
    #v(3pt)
    #text(fill: rgb("#78350F"), size: 9pt)[#body]
  ]
)

#let success-box(title, body) = block(
  fill: rgb("#F0FDF4"),
  stroke: (left: 3.5pt + rgb("#16A34A"), rest: 0.5pt + rgb("#BBF7D0")),
  inset: 10pt,
  radius: (right: 4pt),
  width: 100%,
  above: 8pt,
  below: 8pt,
  [
    #text(fill: rgb("#15803D"), weight: "bold", size: 9.5pt)[#title] \
    #v(3pt)
    #text(fill: rgb("#14532D"), size: 9pt)[#body]
  ]
)

#let danger-box(title, body) = block(
  fill: rgb("#FEF2F2"),
  stroke: (left: 3.5pt + rgb("#DC2626"), rest: 0.5pt + rgb("#FECACA")),
  inset: 10pt,
  radius: (right: 4pt),
  width: 100%,
  above: 8pt,
  below: 8pt,
  [
    #text(fill: rgb("#B91C1C"), weight: "bold", size: 9.5pt)[#title] \
    #v(3pt)
    #text(fill: rgb("#7F1D1D"), size: 9pt)[#body]
  ]
)

#let metric-badge(val, label, accent: rgb("#0D9488")) = block(
  fill: rgb("#F8FAFC"),
  stroke: 1pt + rgb("#E2E8F0"),
  inset: 8pt,
  radius: 6pt,
  width: 100%,
  [
    #align(center)[
      #text(fill: accent, weight: "bold", size: 14pt)[#val] \
      #v(1pt)
      #text(fill: rgb("#64748B"), size: 8pt, weight: "medium")[#label]
    ]
  ]
)

// COVER PAGE
#align(center + top)[
  #v(20pt)
  #rect(
    fill: rgb("#0F172A"),
    radius: 8pt,
    inset: 22pt,
    width: 100%
  )[
    #align(center)[
      #text(fill: rgb("#2DD4BF"), size: 11pt, weight: "bold", tracking: 0.15em)[SYSTEM GUIDE & OPERATIONAL MANUAL] \
      #v(8pt)
      #text(fill: rgb("#F8FAFC"), size: 26pt, weight: "bold")[CoReOS] \
      #v(6pt)
      #text(fill: rgb("#94A3B8"), size: 14pt, weight: "medium")[Conflict-Aware, Self-Healing Multi-Agent AI Operating System] \
      #v(12pt)
      #text(fill: rgb("#CBD5E1"), size: 10pt)[A Comprehensive System Understanding Guide to Modules, Workflows, Telemetry, Metrics, and Empirical Evaluation]
    ]
  ]

  #v(15pt)

  #grid(
    columns: (1fr, 1fr),
    gutter: 14pt,
    rect(
      fill: rgb("#F8FAFC"),
      stroke: 1pt + rgb("#E2E8F0"),
      radius: 6pt,
      inset: 12pt,
      align(left)[
        #text(fill: rgb("#0D9488"), weight: "bold", size: 9pt)[DOCUMENT METADATA] \
        #v(4pt)
        #text(size: 8.5pt)[
          *Document ID:* COREOS-UG-2026-V1 \
          *Version:* 1.0 (Production Master) \
          *Date:* October 2026 \
          *Classification:* Research & Technical Guide \
          *Target File:* `learning_docs/CoReOS_System_Guide.pdf`
        ]
      ]
    ),
    rect(
      fill: rgb("#F8FAFC"),
      stroke: 1pt + rgb("#E2E8F0"),
      radius: 6pt,
      inset: 12pt,
      align(left)[
        #text(fill: rgb("#0369A1"), weight: "bold", size: 9pt)[AUDIENCE & SCOPE] \
        #v(4pt)
        #text(size: 8.5pt)[
          *Primary Audience:* Users, Researchers, Faculty & Teammates \
          *Scope:* System Functionality, Workflows, Metrics & Visuals \
          *Implementation Level:* Strictly Conceptual & Behavioral \
          *Code Syntax:* Excluded by design (No code tutorials)
        ]
      ]
    )
  )

  #v(15pt)

  #rect(
    fill: rgb("#F1F5F9"),
    stroke: (left: 4pt + rgb("#0D9488"), rest: 1pt + rgb("#CBD5E1")),
    radius: (right: 6pt),
    inset: 14pt,
    align(left)[
      #text(fill: rgb("#0F172A"), weight: "bold", size: 10pt)[Executive Summary & Guide Purpose] \
      #v(4pt)
      #text(size: 8.8pt, fill: rgb("#334155"))[
        Modern operating systems traditionally manage compute (CPU), memory (RAM), and storage (I/O) using independent, decoupled controllers. Under volatile multi-tenant workloads, this decoupling induces catastrophic cross-resource interference—such as thrashing-induced CPU collapse and storage channel starvation during memory swapping.

        *CoReOS* introduces an architectural framework that investigates whether *pre-execution conflict prediction* combined with *closed-loop self-healing* can arbitrate multi-agent resource allocations to preserve system stability. This guide provides a complete, beginner-friendly yet technically thorough walkthrough of the system, its architecture, user workflows, telemetry cards, graphs, tables, and scientific findings—explaining *what the system does, how to use it, what its outputs mean, and how to interpret its results without reading source code*.
      ]
    ]
  )
]

#pagebreak()

// TABLE OF CONTENTS
#v(10pt)
#text(size: 16pt, weight: "bold", fill: rgb("#0F172A"))[Table of Contents]
#v(8pt)
#line(length: 100%, stroke: 1pt + rgb("#CBD5E1"))
#v(8pt)

#outline(
  title: none,
  indent: 1.5em,
  depth: 2
)

#v(16pt)
#line(length: 100%, stroke: 0.5pt + rgb("#E2E8F0"))
#v(8pt)

#info-box("How to Navigate This Guide", [
  - *Chapters 1–3* establish core concepts, multi-agent interactions, and the end-to-end user journey.
  - *Chapter 4* examines every page of the running dashboard with authentic application screenshots.
  - *Chapters 5–6* provide comprehensive reference definitions for all 25+ metrics and visualization guides.
  - *Chapters 7–8* map cross-module relationships and present 3 complete worked walkthrough examples.
  - *Chapters 9–10* cover empirical research conclusions, limitations, and quick-reference cheatsheets for presentations.
])

#pagebreak()
'''
