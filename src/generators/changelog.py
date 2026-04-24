import os
import re
import glob
import html
import datetime
import argparse

from owlready2 import World


CATEGORY_ORDER = ["class", "property", "individual"]
CATEGORY_META = {
    "class": {"label": "Classes", "short": "CLS", "item": "Class"},
    "property": {"label": "Propriedades", "short": "PROP", "item": "Property"},
    "individual": {"label": "Individuos", "short": "IND", "item": "Individual"},
}


HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog - AirData Ontology</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(0, 60, 125, 0.08), transparent 28%),
                linear-gradient(180deg, #f6f9fc 0%, #eef3f8 100%);
            color: #1f2937;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .container {
            max-width: 1180px;
            margin: 0 auto;
            padding: 3.5rem 1.5rem 4rem;
            flex: 1;
            width: 100%;
        }

        .hero {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
            gap: 1.5rem;
            align-items: stretch;
            margin-bottom: 2.5rem;
        }

        .hero-panel,
        .summary-panel,
        .controls {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(209, 217, 224, 0.9);
            border-radius: 16px;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }

        .hero-panel {
            padding: 2rem 2.2rem;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: rgba(0, 60, 125, 0.08);
            color: #003C7D;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }

        h1 {
            color: #0f172a;
            font-size: clamp(2rem, 3vw, 2.8rem);
            line-height: 1.1;
            margin-bottom: 0.9rem;
        }

        .hero-text {
            color: #475569;
            font-size: 1rem;
            line-height: 1.75;
            max-width: 62ch;
        }

        .summary-panel {
            padding: 1.6rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 1.2rem;
        }

        .summary-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .summary-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
        }

        .summary-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: #003C7D;
            line-height: 1;
            margin-bottom: 0.35rem;
        }

        .summary-label {
            color: #64748b;
            font-size: 0.9rem;
        }

        .summary-note {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        .controls {
            padding: 1rem 1.1rem;
            margin-bottom: 1.5rem;
            display: grid;
            gap: 0.9rem;
        }

        .control-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 1rem;
            align-items: center;
        }

        .search-wrap {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-width: 0;
        }

        .search-label,
        .filter-label {
            color: #003C7D;
            font-weight: 700;
            font-size: 0.92rem;
            white-space: nowrap;
        }

        .search-input {
            width: 100%;
            min-width: 0;
            border: 1px solid #cbd5e1;
            background: #fff;
            color: #0f172a;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .search-input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        }

        .filter-block {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            align-items: center;
        }

        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }

        .filter-chip {
            border: 1px solid #dbe4ee;
            background: #fff;
            color: #475569;
            border-radius: 999px;
            padding: 0.55rem 0.9rem;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .filter-chip:hover {
            border-color: #93c5fd;
            color: #0f172a;
        }

        .filter-chip.active {
            background: #003C7D;
            border-color: #003C7D;
            color: #fff;
            box-shadow: 0 10px 22px rgba(0, 60, 125, 0.18);
        }

        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .toolbar-note {
            color: #64748b;
            font-size: 0.9rem;
        }

        .toolbar-actions {
            display: flex;
            gap: 0.55rem;
        }

        .toolbar-button {
            border: 1px solid #dbe4ee;
            background: rgba(255, 255, 255, 0.92);
            color: #334155;
            border-radius: 10px;
            padding: 0.6rem 0.85rem;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .toolbar-button:hover {
            border-color: #93c5fd;
            color: #003C7D;
        }

        .timeline {
            position: relative;
            padding-left: 2.25rem;
        }

        .timeline::before {
            content: "";
            position: absolute;
            left: 0.6rem;
            top: 0.4rem;
            bottom: 0.4rem;
            width: 2px;
            background: linear-gradient(180deg, #93c5fd 0%, #cbd5e1 100%);
        }

        .version-card {
            position: relative;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(209, 217, 224, 0.9);
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.6rem;
            overflow: hidden;
        }

        .version-card.latest {
            border-color: rgba(14, 165, 233, 0.4);
            box-shadow: 0 22px 55px rgba(14, 165, 233, 0.12);
        }

        .version-card::before {
            content: "";
            position: absolute;
            left: -1.95rem;
            top: 1.7rem;
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: #0ea5e9;
            border: 4px solid #dbeafe;
            box-shadow: 0 0 0 6px rgba(14, 165, 233, 0.12);
        }

        .version-header {
            padding: 1.35rem 1.5rem 1rem;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 1rem;
            border-bottom: 1px solid #eef2f7;
            background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.92));
        }

        .version-meta {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }

        .version-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
        }

        .version-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .version-date {
            color: #003C7D;
            background: rgba(0, 60, 125, 0.08);
            border: 1px solid rgba(0, 60, 125, 0.12);
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            white-space: nowrap;
            font-size: 0.85rem;
            font-weight: 700;
            height: fit-content;
        }

        .latest-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            width: fit-content;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: rgba(14, 165, 233, 0.12);
            color: #0369a1;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .version-metrics {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .metric-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            border-radius: 999px;
            padding: 0.35rem 0.7rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .metric-chip strong {
            color: #003C7D;
        }

        .change-groups {
            padding: 1.1rem 1.3rem 1.35rem;
            display: grid;
            gap: 1rem;
        }

        .change-group {
            background: #fcfdff;
            border: 1px solid #e7edf4;
            border-radius: 14px;
            overflow: hidden;
        }

        .change-toggle {
            width: 100%;
            border: none;
            background: transparent;
            padding: 1rem 1.05rem 1rem 1.15rem;
            cursor: pointer;
            text-align: left;
        }

        .change-title {
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.65rem;
            color: #0f172a;
        }

        .change-count {
            margin-left: auto;
            color: #64748b;
            font-size: 0.86rem;
            font-weight: 600;
        }

        .badge {
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .badge-added { background: #dcfce7; color: #166534; }
        .badge-removed { background: #fee2e2; color: #b91c1c; }
        .badge-changed { background: #ffedd5; color: #c2410c; }

        .toggle-icon {
            margin-left: 0.15rem;
            color: #64748b;
            font-size: 0.8rem;
            transition: transform 0.2s ease;
        }

        .change-group.collapsed .toggle-icon {
            transform: rotate(-90deg);
        }

        .change-group-body {
            padding: 0 1.05rem 1rem 1.15rem;
            display: grid;
            gap: 0.85rem;
        }

        .change-group.collapsed .change-group-body {
            display: none;
        }

        .category-section {
            border: 1px solid #edf2f7;
            background: #ffffff;
            border-radius: 12px;
            padding: 0.85rem;
        }

        .category-header {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.75rem;
        }

        .category-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2.3rem;
            padding: 0.22rem 0.5rem;
            border-radius: 999px;
            background: rgba(0, 60, 125, 0.08);
            color: #003C7D;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .category-title {
            font-size: 0.92rem;
            font-weight: 800;
            color: #0f172a;
        }

        .category-count {
            margin-left: auto;
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 700;
        }

        .tree-list,
        .tree-list ul {
            list-style: none;
            margin: 0;
            padding-left: 1.2rem;
            position: relative;
        }

        .tree-list {
            padding-left: 0.3rem;
        }

        .tree-list ul {
            margin-top: 0.7rem;
        }

        .tree-list li {
            position: relative;
            padding-left: 1.15rem;
            margin-bottom: 0.8rem;
        }

        .tree-list li:last-child {
            margin-bottom: 0;
        }

        .tree-list li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0.75rem;
            width: 0.7rem;
            height: 1px;
            background: #94a3b8;
        }

        .tree-list li::after {
            content: "";
            position: absolute;
            left: 0;
            top: -0.55rem;
            bottom: -0.55rem;
            width: 1px;
            background: #cbd5e1;
        }

        .tree-list li:last-child::after {
            bottom: calc(100% - 0.75rem);
        }

        .tree-item {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.55rem;
            padding: 0.7rem 0.8rem;
            border-radius: 12px;
            background: white;
            border: 1px solid #edf2f7;
        }

        .tree-item-head {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
        }

        .entity-marker {
            width: 0.7rem;
            height: 0.7rem;
            border-radius: 999px;
            flex: 0 0 auto;
        }

        .marker-class {
            background: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        }

        .marker-property {
            background: #7c3aed;
            box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.12);
        }

        .marker-individual {
            background: #ea580c;
            box-shadow: 0 0 0 4px rgba(234, 88, 12, 0.12);
        }

        .entity-type-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.22rem 0.48rem;
            border-radius: 999px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .entity-name {
            font-family: "Consolas", "SFMono-Regular", "Courier New", monospace;
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
        }

        .item-iri {
            color: #64748b;
            font-size: 0.8rem;
            word-break: break-all;
            width: 100%;
            padding-left: 1.3rem;
        }

        .change-detail {
            font-size: 0.9rem;
            color: #475569;
            line-height: 1.6;
        }

        .entity-node {
            display: grid;
            gap: 0.55rem;
        }

        .entity-toggle {
            width: 100%;
            border: none;
            background: transparent;
            padding: 0;
            text-align: left;
            cursor: pointer;
        }

        .entity-toggle .tree-item {
            transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
        }

        .entity-toggle:hover .tree-item {
            border-color: #bfdbfe;
            box-shadow: 0 10px 24px rgba(59, 130, 246, 0.08);
            background: #fcfdff;
        }

        .entity-toggle-icon {
            margin-left: auto;
            color: #64748b;
            font-size: 0.78rem;
            transition: transform 0.2s ease;
        }

        .entity-node.collapsed .entity-toggle-icon {
            transform: rotate(-90deg);
        }

        .entity-children {
            padding-left: 0.5rem;
        }

        .entity-node.collapsed .entity-children {
            display: none;
        }

        .change-detail .old-value {
            color: #b91c1c;
            text-decoration: line-through;
            margin-right: 0.35rem;
        }

        .change-detail .new-value {
            color: #166534;
            font-weight: 700;
            margin-left: 0.35rem;
        }

        .empty-state {
            padding: 2.2rem;
            text-align: center;
            color: #64748b;
            font-style: italic;
            background: rgba(255, 255, 255, 0.9);
            border: 1px dashed #cbd5e1;
            border-radius: 16px;
        }

        .empty-results {
            display: none;
            margin-top: 1.2rem;
        }

        .empty-results.visible {
            display: block;
        }

        @media (max-width: 900px) {
            .hero {
                grid-template-columns: 1fr;
            }

            .control-row {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 720px) {
            .container {
                padding: 2rem 1rem 3rem;
            }

            .timeline {
                padding-left: 1.55rem;
            }

            .timeline::before {
                left: 0.35rem;
            }

            .version-card::before {
                left: -1.3rem;
            }

            .version-header {
                grid-template-columns: 1fr;
            }

            .toolbar {
                flex-direction: column;
                align-items: flex-start;
            }

            .toolbar-actions {
                width: 100%;
                flex-wrap: wrap;
            }

            .item-iri {
                padding-left: 0;
            }
        }

        @media (max-width: 560px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <main class="container">
        <section class="hero">
            <div class="hero-panel">
                <div class="eyebrow">Evolucao da Ontologia</div>
                <h1>Historico de Mudancas</h1>
                <p class="hero-text">
                    Acompanhe a evolucao da AirData Ontology em uma linha do tempo por versao, com separacao semantica entre classes, propriedades e individuos.
                </p>
            </div>
            <aside class="summary-panel">
                <div class="summary-title">Resumo do Changelog</div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-value">{{version_count}}</div>
                        <div class="summary-label">comparacoes</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{{entity_delta}}</div>
                        <div class="summary-label">mudancas rastreadas</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{{class_delta}}</div>
                        <div class="summary-label">classes afetadas</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{{property_delta}}</div>
                        <div class="summary-label">propriedades afetadas</div>
                    </div>
                </div>
                <p class="summary-note">
                    Use os filtros para navegar por tipo de mudanca e por categoria semantica, facilitando a revisao de releases maiores.
                </p>
            </aside>
        </section>

        <section class="controls">
            <div class="control-row">
                <div class="search-wrap">
                    <label class="search-label" for="changelog-search">Buscar</label>
                    <input
                        id="changelog-search"
                        class="search-input"
                        type="search"
                        placeholder="Filtre por nome da entidade, IRI ou versao..."
                        autocomplete="off"
                    >
                </div>
                <div class="filter-block">
                    <span class="filter-label">Mudanca</span>
                    <div class="filters" role="group" aria-label="Filtros por tipo de mudanca">
                        <button type="button" class="filter-chip active" data-filter="all">Tudo</button>
                        <button type="button" class="filter-chip" data-filter="added">Adicionados</button>
                        <button type="button" class="filter-chip" data-filter="removed">Removidos</button>
                        <button type="button" class="filter-chip" data-filter="changed">Alterados</button>
                    </div>
                </div>
            </div>
            <div class="control-row">
                <div class="filter-block">
                    <span class="filter-label">Categoria</span>
                    <div class="filters" role="group" aria-label="Filtros por categoria semantica">
                        <button type="button" class="filter-chip active" data-category="all">Tudo</button>
                        <button type="button" class="filter-chip" data-category="class">Classes</button>
                        <button type="button" class="filter-chip" data-category="property">Propriedades</button>
                        <button type="button" class="filter-chip" data-category="individual">Individuos</button>
                    </div>
                </div>
            </div>
        </section>

        <section class="toolbar">
            <div class="toolbar-note" id="results-summary">Mostrando todas as versoes e grupos de mudanca.</div>
            <div class="toolbar-actions">
                <button type="button" class="toolbar-button" id="expand-all">Expandir tudo</button>
                <button type="button" class="toolbar-button" id="collapse-all">Recolher grupos</button>
            </div>
        </section>

        <section class="timeline">
"""

HTML_END = """
        </section>
        <div class="empty-state empty-results" id="empty-results">
            Nenhum resultado encontrado para os filtros atuais.
        </div>
    </main>
    <script>
        (function () {
            const searchInput = document.getElementById("changelog-search");
            const typeButtons = Array.from(document.querySelectorAll(".filter-chip[data-filter]"));
            const categoryButtons = Array.from(document.querySelectorAll(".filter-chip[data-category]"));
            const versionCards = Array.from(document.querySelectorAll(".version-card"));
            const resultSummary = document.getElementById("results-summary");
            const emptyResults = document.getElementById("empty-results");
            const expandAllButton = document.getElementById("expand-all");
            const collapseAllButton = document.getElementById("collapse-all");
            let activeFilter = "all";
            let activeCategory = "all";

            function normalize(value) {
                return (value || "")
                    .toString()
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .toLowerCase();
            }

            function updateSummary(visibleCards, visibleGroups, visibleSections) {
                if (!visibleGroups) {
                    resultSummary.textContent = "Nenhum grupo encontrado com os filtros atuais.";
                    return;
                }

                const cardLabel = visibleCards === 1 ? "versao" : "versoes";
                const groupLabel = visibleGroups === 1 ? "grupo" : "grupos";
                const sectionLabel = visibleSections === 1 ? "categoria" : "categorias";
                resultSummary.textContent = `Mostrando ${visibleCards} ${cardLabel}, ${visibleGroups} ${groupLabel} e ${visibleSections} ${sectionLabel} visiveis.`;
            }

            function applyFilters() {
                const query = normalize(searchInput.value);
                let visibleCards = 0;
                let visibleGroups = 0;
                let visibleSections = 0;

                versionCards.forEach((card) => {
                    const groups = Array.from(card.querySelectorAll(".change-group"));
                    let cardHasVisibleGroup = false;

                    groups.forEach((group) => {
                        const groupType = group.dataset.groupType;
                        const sections = Array.from(group.querySelectorAll(".category-section"));
                        let groupHasVisibleSection = false;

                        sections.forEach((section) => {
                            const sectionCategory = section.dataset.entityCategory;
                            const sectionText = normalize(section.dataset.searchText);
                            const matchesCategory = activeCategory === "all" || sectionCategory === activeCategory;
                            const matchesSearch = !query || sectionText.includes(query);
                            const visibleSection = matchesCategory && matchesSearch;

                            section.style.display = visibleSection ? "" : "none";
                            if (visibleSection) {
                                groupHasVisibleSection = true;
                                visibleSections += 1;
                            }
                        });

                        const groupText = normalize(group.dataset.searchText);
                        const matchesFilter = activeFilter === "all" || groupType === activeFilter;
                        const matchesSearch = !query || groupText.includes(query);
                        const visibleGroup = matchesFilter && matchesSearch && groupHasVisibleSection;

                        group.style.display = visibleGroup ? "" : "none";
                        if (visibleGroup) {
                            cardHasVisibleGroup = true;
                            visibleGroups += 1;
                        }
                    });

                    const versionText = normalize(card.dataset.versionText);
                    const versionMatches = !query || versionText.includes(query);
                    const showCard = cardHasVisibleGroup || (versionMatches && activeFilter === "all" && activeCategory === "all");
                    card.style.display = showCard ? "" : "none";

                    if (showCard) {
                        visibleCards += 1;
                    }
                });

                updateSummary(visibleCards, visibleGroups, visibleSections);
                emptyResults.classList.toggle("visible", visibleCards === 0);
            }

            function setCollapsedState(collapsed) {
                document.querySelectorAll(".change-group").forEach((group) => {
                    group.classList.toggle("collapsed", collapsed);
                    const button = group.querySelector(".change-toggle");
                    if (button) {
                        button.setAttribute("aria-expanded", collapsed ? "false" : "true");
                    }
                });
            }

            typeButtons.forEach((button) => {
                button.addEventListener("click", function () {
                    activeFilter = this.dataset.filter;
                    typeButtons.forEach((item) => item.classList.toggle("active", item === this));
                    applyFilters();
                });
            });

            categoryButtons.forEach((button) => {
                button.addEventListener("click", function () {
                    activeCategory = this.dataset.category;
                    categoryButtons.forEach((item) => item.classList.toggle("active", item === this));
                    applyFilters();
                });
            });

            document.querySelectorAll(".change-toggle").forEach((button) => {
                button.addEventListener("click", function () {
                    const group = this.closest(".change-group");
                    const collapsed = group.classList.toggle("collapsed");
                    this.setAttribute("aria-expanded", collapsed ? "false" : "true");
                });
            });

            document.querySelectorAll(".entity-toggle").forEach((button) => {
                button.addEventListener("click", function () {
                    const node = this.closest(".entity-node");
                    const collapsed = node.classList.toggle("collapsed");
                    this.setAttribute("aria-expanded", collapsed ? "false" : "true");
                });
            });

            expandAllButton.addEventListener("click", function () {
                setCollapsedState(false);
            });

            collapseAllButton.addEventListener("click", function () {
                setCollapsedState(true);
            });

            searchInput.addEventListener("input", applyFilters);
            applyFilters();
        })();
    </script>
</body>
</html>
"""


def get_owl_files(owl_dir):
    files = glob.glob(f"{owl_dir}/*.owl")
    files.sort(key=os.path.getctime, reverse=True)
    return files


def infer_category(entity):
    entity_type = type(entity).__name__
    if entity_type == "ThingClass":
        return "class"
    if entity_type.endswith("PropertyClass"):
        return "property"
    return "individual"


def get_entities(onto):
    entities = {}

    def add_entity_fingerprint(entity, category):
        iri = str(entity.iri)
        label = str(entity.label) if hasattr(entity, "label") else None
        comment = str(entity.comment) if hasattr(entity, "comment") else None

        if isinstance(label, list):
            label = label[0] if label else None
        if isinstance(comment, list):
            comment = comment[0] if comment else None

        entities[iri] = {
            "iri": iri,
            "label": label,
            "comment": comment,
            "category": category,
        }

    for cls in onto.classes():
        add_entity_fingerprint(cls, infer_category(cls))
    for prop in onto.properties():
        add_entity_fingerprint(prop, infer_category(prop))
    for individual in onto.individuals():
        add_entity_fingerprint(individual, "individual")

    return entities


def compare_versions(new_file, old_file):
    print(f"Comparando: {os.path.basename(new_file)} vs {os.path.basename(old_file)}")

    world_new = World()
    onto_new = world_new.get_ontology(new_file).load()
    entities_new_map = get_entities(onto_new)

    world_old = World()
    onto_old = world_old.get_ontology(old_file).load()
    entities_old_map = get_entities(onto_old)

    iris_new = set(entities_new_map.keys())
    iris_old = set(entities_old_map.keys())

    added_iris = iris_new - iris_old
    removed_iris = iris_old - iris_new
    common_iris = iris_new.intersection(iris_old)

    added_entities = [entities_new_map[iri] for iri in added_iris]
    removed_entities = [entities_old_map[iri] for iri in removed_iris]
    changed_entities = []

    for iri in common_iris:
        fingerprint_new = entities_new_map[iri]
        fingerprint_old = entities_old_map[iri]

        changes = {}
        if fingerprint_new["label"] != fingerprint_old["label"]:
            changes["label"] = {
                "old": fingerprint_old["label"],
                "new": fingerprint_new["label"],
            }
        if fingerprint_new["comment"] != fingerprint_old["comment"]:
            changes["comment"] = {
                "old": fingerprint_old["comment"],
                "new": fingerprint_new["comment"],
            }

        if changes:
            changed_entities.append({
                "entity": fingerprint_new,
                "changes": changes,
            })

    return {
        "new_file": os.path.basename(new_file),
        "old_file": os.path.basename(old_file),
        "date": datetime.datetime.fromtimestamp(os.path.getctime(new_file)).strftime("%d/%m/%Y"),
        "added": sorted(added_entities, key=lambda x: (x["category"], x["iri"])),
        "removed": sorted(removed_entities, key=lambda x: (x["category"], x["iri"])),
        "changed": sorted(changed_entities, key=lambda x: (x["entity"]["category"], x["entity"]["iri"])),
    }


def esc(value):
    return html.escape(str(value), quote=True)


def normalize_search_text(value):
    return " ".join(str(value).lower().split())


def strip_html(value):
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def render_entity_shell(entity_data, include_toggle=False):
    category = entity_data["category"]
    category_meta = CATEGORY_META[category]
    marker_class = f"marker-{category}"
    name = esc(entity_data["iri"].split("#")[-1])
    iri = esc(entity_data["iri"])
    toggle = '<span class="entity-toggle-icon">▾</span>' if include_toggle else ""

    return (
        '<div class="tree-item">'
        '<div class="tree-item-head">'
        f'<span class="entity-marker {marker_class}"></span>'
        f'<span class="entity-type-pill">{category_meta["item"]}</span>'
        f'<span class="entity-name">{name}</span>'
        f'{toggle}'
        '</div>'
        f'<span class="item-iri">{iri}</span>'
        '</div>'
    )


def format_entity_item(entity_data):
    return f'<li>{render_entity_shell(entity_data)}</li>'


def render_category_section(category_key, items_html, count):
    category_meta = CATEGORY_META[category_key]
    search_text = normalize_search_text(strip_html(items_html))
    return f"""
                    <section class="category-section" data-entity-category="{category_key}" data-search-text="{esc(search_text)}">
                        <div class="category-header">
                            <span class="category-badge">{category_meta['short']}</span>
                            <div class="category-title">{category_meta['label']}</div>
                            <div class="category-count">{count} itens</div>
                        </div>
                        <ul class="tree-list">
                            {items_html}
                        </ul>
                    </section>
"""


def render_change_group(badge_class, badge_text, title, categorized_sections, count):
    group_type = badge_class.replace("badge-", "")
    sections_html = []
    search_chunks = [badge_text, title]

    for category_key in CATEGORY_ORDER:
        if category_key not in categorized_sections:
            continue
        items = categorized_sections[category_key]
        sections_html.append(render_category_section(category_key, items["html"], items["count"]))
        search_chunks.append(CATEGORY_META[category_key]["label"])
        search_chunks.append(items["search"])

    search_text = normalize_search_text(" ".join(search_chunks))
    return f"""
            <div class="change-group" data-group-type="{group_type}" data-search-text="{esc(search_text)}">
                <button type="button" class="change-toggle" aria-expanded="true">
                    <div class="change-title">
                        <span class="badge {badge_class}">{badge_text}</span>
                        {title}
                        <span class="change-count">{count} itens</span>
                        <span class="toggle-icon">▾</span>
                    </div>
                </button>
                <div class="change-group-body">
                    {''.join(sections_html)}
                </div>
            </div>
"""


def group_entities_by_category(entities):
    categorized = {}
    for entity_data in entities:
        category = entity_data["category"]
        categorized.setdefault(category, [])
        categorized[category].append(format_entity_item(entity_data))
    return {
        category: {
            "html": "".join(items),
            "count": len(items),
            "search": normalize_search_text(strip_html(" ".join(items))),
        }
        for category, items in categorized.items()
    }


def group_changed_by_category(changed_entities):
    categorized = {}
    for change_data in changed_entities:
        entity = change_data["entity"]
        category = entity["category"]
        categorized.setdefault(category, [])

        detail_items = []
        if "label" in change_data["changes"]:
            old_label = esc(change_data["changes"]["label"]["old"] if change_data["changes"]["label"]["old"] is not None else "N/A")
            new_label = esc(change_data["changes"]["label"]["new"] if change_data["changes"]["label"]["new"] is not None else "N/A")
            detail_items.append(
                '<li><div class="tree-item change-detail">'
                f'Label: <span class="old-value">{old_label}</span> → <span class="new-value">{new_label}</span>'
                '</div></li>'
            )
        if "comment" in change_data["changes"]:
            old_comment = esc(change_data["changes"]["comment"]["old"] if change_data["changes"]["comment"]["old"] is not None else "N/A")
            new_comment = esc(change_data["changes"]["comment"]["new"] if change_data["changes"]["comment"]["new"] is not None else "N/A")
            detail_items.append(
                '<li><div class="tree-item change-detail">'
                f'Comment: <span class="old-value">{old_comment}</span> → <span class="new-value">{new_comment}</span>'
                '</div></li>'
                )

        categorized[category].append(
            '<li>'
            '<div class="entity-node">'
            '<button type="button" class="entity-toggle" aria-expanded="true">'
            f'{render_entity_shell(entity, include_toggle=True)}'
            '</button>'
            '<div class="entity-children">'
            '<ul class="tree-list">'
            f'{"".join(detail_items)}'
            '</ul>'
            '</div>'
            '</div>'
            '</li>'
        )

    return {
        category: {
            "html": "".join(items),
            "count": len(items),
            "search": normalize_search_text(strip_html(" ".join(items))),
        }
        for category, items in categorized.items()
    }


def build_version_metrics(diff_data):
    counts = {category: 0 for category in CATEGORY_ORDER}
    for bucket in ("added", "removed"):
        for entity in diff_data[bucket]:
            counts[entity["category"]] += 1
    for changed in diff_data["changed"]:
        counts[changed["entity"]["category"]] += 1

    parts = []
    for category in CATEGORY_ORDER:
        total = counts[category]
        if not total:
            continue
        parts.append(
            f'<span class="metric-chip">{CATEGORY_META[category]["label"]}: <strong>{total}</strong></span>'
        )
    return "".join(parts)


def generate_html_card(diff_data):
    total_changes = len(diff_data["added"]) + len(diff_data["removed"]) + len(diff_data["changed"])
    card_classes = ["version-card"]
    latest_badge = ""
    if diff_data.get("is_latest"):
        card_classes.append("latest")
        latest_badge = '<div class="latest-badge">Mais recente</div>'

    html_parts = [f"""
        <div class="{' '.join(card_classes)}" data-version-text="{esc(normalize_search_text(f"{diff_data['new_file']} {diff_data['old_file']} {diff_data['date']}"))}">
            <div class="version-header">
                <div class="version-meta">
                    {latest_badge}
                    <div class="version-title">{esc(diff_data["new_file"])}</div>
                    <div class="version-subtitle">Comparado com {esc(diff_data["old_file"])}</div>
                    <div class="version-metrics">{build_version_metrics(diff_data)}</div>
                </div>
                <div class="version-date">{esc(diff_data["date"])} • {total_changes} mudancas</div>
            </div>
            <div class="change-groups">
"""]

    has_changes = False

    if diff_data["added"]:
        has_changes = True
        categorized = group_entities_by_category(diff_data["added"])
        html_parts.append(render_change_group("badge-added", "ADICIONADO", "Novas Entidades", categorized, len(diff_data["added"])))

    if diff_data["removed"]:
        has_changes = True
        categorized = group_entities_by_category(diff_data["removed"])
        html_parts.append(render_change_group("badge-removed", "REMOVIDO", "Entidades Excluidas", categorized, len(diff_data["removed"])))

    if diff_data["changed"]:
        has_changes = True
        categorized = group_changed_by_category(diff_data["changed"])
        html_parts.append(render_change_group("badge-changed", "ALTERADO", "Entidades Modificadas", categorized, len(diff_data["changed"])))

    if not has_changes:
        html_parts.append('<div class="empty-state">Nenhuma mudanca estrutural detectada.</div>')

    html_parts.append("""
            </div>
        </div>
""")
    return "".join(html_parts)


def main(owl_dir, output_file):
    files = get_owl_files(owl_dir)

    if len(files) < 2:
        full_html = (
            HTML_TEMPLATE_START
            .replace("{{version_count}}", "0")
            .replace("{{entity_delta}}", "0")
            .replace("{{class_delta}}", "0")
            .replace("{{property_delta}}", "0")
            + '<div class="empty-state">Aguardando mais versoes para gerar historico.</div>'
            + HTML_END
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        return

    content_html = ""
    summary = {
        "version_count": len(files) - 1,
        "entity_delta": 0,
        "class_delta": 0,
        "property_delta": 0,
    }

    for i in range(len(files) - 1):
        try:
            diff = compare_versions(files[i], files[i + 1])
            diff["is_latest"] = i == 0

            summary["entity_delta"] += len(diff["added"]) + len(diff["removed"]) + len(diff["changed"])
            for entity in diff["added"] + diff["removed"]:
                if entity["category"] == "class":
                    summary["class_delta"] += 1
                elif entity["category"] == "property":
                    summary["property_delta"] += 1
            for change in diff["changed"]:
                if change["entity"]["category"] == "class":
                    summary["class_delta"] += 1
                elif change["entity"]["category"] == "property":
                    summary["property_delta"] += 1

            content_html += generate_html_card(diff)
        except Exception as e:
            print(f"Erro ao comparar {files[i]} e {files[i + 1]}: {e}")

    full_html = (
        HTML_TEMPLATE_START
        .replace("{{version_count}}", str(summary["version_count"]))
        .replace("{{entity_delta}}", str(summary["entity_delta"]))
        .replace("{{class_delta}}", str(summary["class_delta"]))
        .replace("{{property_delta}}", str(summary["property_delta"]))
        + content_html
        + HTML_END
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"Changelog gerado em {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um changelog HTML comparando versoes de ontologias.")
    parser.add_argument("--owl-dir", required=True, help="Diretorio contendo os arquivos .owl.")
    parser.add_argument("--output-file", required=True, help="Caminho para o arquivo HTML de saida.")

    args = parser.parse_args()
    main(args.owl_dir, args.output_file)
