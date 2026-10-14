"""
Clean utility script to ensure all underscores in text mode in main.tex are escaped properly.
"""
import re

with open('research_paper/main.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
in_verbatim = False

for line in lines:
    if r'\begin{verbatim}' in line:
        in_verbatim = True
        out.append(line)
        continue
    if r'\end{verbatim}' in line:
        in_verbatim = False
        out.append(line)
        continue
    if in_verbatim:
        out.append(line)
        continue

    # If it's a comment or label or graphicspath, leave it
    if line.strip().startswith('%') or r'\label{' in line or r'\includegraphics' in line or r'\bibliography' in line or r'\graphicspath' in line:
        out.append(line)
        continue

    # Replace unescaped candidate names and workloads in text
    cands = ['A_Conventional', 'B_IndependentAgents', 'C_CoordNoConflict', 'D_ConflictNoHealing',
             'E_CompleteCoReOS', 'F_ImprovedRL', 'G_ChampionCoReOS', 'H_OriginalRL']
    for c in cands:
        esc_c = c.replace('_', r'\_')
        line = line.replace(c, esc_c)

    wls = ['steady_state', 'cpu_spike', 'memory_thrashing', 'io_bottleneck', 'adversarial_stress']
    for w in wls:
        esc_w = w.replace('_', r'\_')
        line = line.replace(w, esc_w)

    # Replace backticks
    line = line.replace('`research_paper/figures/`', r'\texttt{research\_paper/figures/}')
    line = line.replace('`reports/optimization/`', r'\texttt{reports/optimization/}')
    line = line.replace('`main.pdf`', r'\texttt{main.pdf}')
    line = line.replace('research_paper/figures/', r'research\_paper/figures/')
    line = line.replace('reports/optimization/', r'reports/optimization/')

    # Fix specific terms
    line = line.replace('sched_ext', r'sched\_ext')

    out.append(line)

with open('research_paper/main.tex', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Successfully sanitized research_paper/main.tex")
