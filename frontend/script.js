/**
 * AI Research Assistant — Frontend Logic
 * Handles both Research and Web Scraper views.
 */

// =============================================
// State
// =============================================
let currentView = 'research';
let currentPapers = [];
let lastScrapeData = null;

// =============================================
// DOM References
// =============================================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// Nav
const navResearch = $('#navResearch');
const navScraper = $('#navScraper');
const researchView = $('#researchView');
const scraperView = $('#scraperView');

// Research
const researchQuery = $('#researchQuery');
const searchBtn = $('#searchBtn');
const fullPipelineBtn = $('#fullPipelineBtn');
const clearResearchBtn = $('#clearResearchBtn');
const maxResultsSelect = $('#maxResults');
const pipelineProgress = $('#pipelineProgress');
const progressFill = $('#progressFill');
const statsRow = $('#statsRow');
const researchResults = $('#researchResults');
const papersGrid = $('#papersGrid');
const resultsCount = $('#resultsCount');
const totalPapersEl = $('#totalPapers .stat-value');

// Scraper
const urlInput = $('#urlInput');
const scrapeBtn = $('#scrapeBtn');
const clearBtn = $('#clearBtn');
const scraperResults = $('#scraperResults');

// Modal
const paperModal = $('#paperModal');
const modalClose = $('#modalClose');
const modalBody = $('#modalBody');

// Toast
const toast = $('#toast');
const toastMessage = $('#toastMessage');

// =============================================
// Navigation
// =============================================
$$('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const view = tab.dataset.view;
        $$('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        $$('.view-panel').forEach(p => p.classList.remove('active'));
        $(`#${view}View`).classList.add('active');
        currentView = view;
    });
});

// =============================================
// Source Toggles
// =============================================
$$('.chip-option').forEach(chip => {
    chip.addEventListener('click', () => {
        $$('.chip-option').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        chip.querySelector('input').checked = true;
    });
});

// =============================================
// Research — Quick Search
// =============================================
searchBtn.addEventListener('click', async () => {
    const query = researchQuery.value.trim();
    if (!query) { showToast('Please enter a research topic', 'error'); return; }

    searchBtn.classList.add('loading');
    pipelineProgress.style.display = 'none';
    researchResults.style.display = 'none';
    statsRow.style.display = 'none';

    try {
        const sources = getSelectedSource();
        const maxResults = parseInt(maxResultsSelect.value);

        const response = await fetch('/research/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, max_results: maxResults, sources, download_pdfs: false, summarize: false }),
        });

        const data = await response.json();

        if (data.success !== false) {
            currentPapers = data.papers || [];
            renderPapers(currentPapers);
            updateStats({
                total: currentPapers.length,
                arxiv: currentPapers.filter(p => p.source === 'arxiv').length,
                semantic_scholar: currentPapers.filter(p => p.source === 'semantic_scholar').length,
                pdfs_downloaded: 0,
                summarized: 0,
            });
            showToast(`Found ${currentPapers.length} papers`, 'success');
        } else {
            showToast(data.message || 'No papers found', 'error');
        }
    } catch (err) {
        showToast(`Search failed: ${err.message}`, 'error');
    } finally {
        searchBtn.classList.remove('loading');
    }
});

// =============================================
// Research — Full Pipeline
// =============================================
fullPipelineBtn.addEventListener('click', async () => {
    const query = researchQuery.value.trim();
    if (!query) { showToast('Please enter a research topic', 'error'); return; }

    fullPipelineBtn.classList.add('loading');
    pipelineProgress.style.display = 'block';
    researchResults.style.display = 'none';
    statsRow.style.display = 'none';

    // Animate pipeline steps
    animatePipeline();

    try {
        const sources = getSelectedSource();
        const maxResults = parseInt(maxResultsSelect.value);

        const response = await fetch('/research/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, max_results: maxResults, sources, download_pdfs: true, summarize: true }),
        });

        const data = await response.json();

        // Complete pipeline animation
        completePipeline();

        if (data.success) {
            currentPapers = data.papers || [];
            renderPapers(currentPapers);
            updateStats(data.stats);
            totalPapersEl.textContent = data.stats.total || currentPapers.length;
            showToast(`Pipeline complete! ${currentPapers.length} papers processed`, 'success');
        } else {
            showToast(data.message || 'Pipeline failed', 'error');
        }
    } catch (err) {
        showToast(`Pipeline failed: ${err.message}`, 'error');
    } finally {
        fullPipelineBtn.classList.remove('loading');
    }
});

// =============================================
// Research — Render Papers
// =============================================
function renderPapers(papers) {
    papersGrid.innerHTML = '';

    if (!papers.length) {
        papersGrid.innerHTML = `<div class="no-results" style="text-align: center; padding: 3rem; color: var(--text-muted);">No papers found. Try a different query.</div>`;
        researchResults.style.display = 'block';
        return;
    }

    papers.forEach((paper, index) => {
        const card = document.createElement('div');
        card.className = 'paper-card';
        card.setAttribute('data-index', index);

        const authors = (paper.authors || []).slice(0, 4).join(', ') + (paper.authors?.length > 4 ? ' et al.' : '');
        const sourceClass = paper.source || 'arxiv';
        const sourceLabel = paper.source === 'semantic_scholar' ? 'Semantic Scholar' : 'arXiv';
        const year = paper.year ? ` · ${paper.year}` : '';
        const citations = paper.citation_count ? ` · ${paper.citation_count} citations` : '';
        const hasSummary = paper.summary && (typeof paper.summary === 'object' ? paper.summary.summary : paper.summary);
        const hasPdf = paper.pdf_url;

        card.innerHTML = `
            <div class="paper-header">
                <h3 class="paper-title">${escapeHtml(paper.title || 'Untitled')}</h3>
                <span class="source-badge ${sourceClass}">${sourceLabel}</span>
            </div>
            <div class="paper-authors">${escapeHtml(authors)}</div>
            <div class="paper-abstract">${escapeHtml(paper.abstract || 'No abstract available.')}</div>
            <div class="paper-meta">
                ${year ? `<span class="paper-meta-item"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${paper.year}</span>` : ''}
                ${citations ? `<span class="paper-meta-item"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>${paper.citation_count} cited</span>` : ''}
                ${hasPdf ? `<a href="${paper.pdf_url}" target="_blank" class="paper-meta-item" style="color: var(--success);" onclick="event.stopPropagation()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>PDF</a>` : ''}
                ${hasSummary ? `<button class="paper-summary-toggle" onclick="event.stopPropagation(); toggleSummary(${index})">🧠 Summary</button>` : ''}
            </div>
            ${hasSummary ? `<div class="paper-summary" id="summary-${index}">${formatSummary(paper.summary)}</div>` : ''}
        `;

        card.addEventListener('click', () => openPaperModal(paper));
        papersGrid.appendChild(card);
    });

    resultsCount.textContent = `${papers.length} papers`;
    researchResults.style.display = 'block';
}

function toggleSummary(index) {
    const el = document.getElementById(`summary-${index}`);
    if (el) el.classList.toggle('visible');
}

function formatSummary(summary) {
    if (!summary) return '';
    if (typeof summary === 'string') return `<p>${escapeHtml(summary)}</p>`;

    let html = '';
    if (summary.summary) html += `<h4>Summary</h4><p>${escapeHtml(summary.summary)}</p>`;
    if (summary.key_findings) html += `<h4>Key Findings</h4><p>${escapeHtml(summary.key_findings)}</p>`;
    if (summary.methodology) html += `<h4>Methodology</h4><p>${escapeHtml(summary.methodology)}</p>`;
    if (summary.conclusions) html += `<h4>Conclusions</h4><p>${escapeHtml(summary.conclusions)}</p>`;
    return html || `<p>${escapeHtml(summary.raw_summary || '')}</p>`;
}

// =============================================
// Paper Modal
// =============================================
function openPaperModal(paper) {
    const authors = (paper.authors || []).join(', ');
    const sourceLabel = paper.source === 'semantic_scholar' ? 'Semantic Scholar' : 'arXiv';

    let summaryHtml = '';
    if (paper.summary) {
        summaryHtml = `
            <div class="modal-section">
                <div class="modal-section-title">AI Summary</div>
                <div class="modal-section-content">${formatSummary(paper.summary)}</div>
            </div>
        `;
    }

    modalBody.innerHTML = `
        <span class="source-badge ${paper.source}" style="margin-bottom: 0.75rem; display: inline-block;">${sourceLabel}</span>
        <h2>${escapeHtml(paper.title || 'Untitled')}</h2>
        <div class="paper-authors" style="margin-bottom: 1rem; -webkit-line-clamp: unset;">${escapeHtml(authors)}</div>
        
        ${paper.year ? `<div class="paper-meta-item" style="margin-bottom: 1rem;"><strong>Year:</strong> ${paper.year}</div>` : ''}
        ${paper.citation_count ? `<div class="paper-meta-item" style="margin-bottom: 1rem;"><strong>Citations:</strong> ${paper.citation_count}</div>` : ''}
        
        <div class="modal-section">
            <div class="modal-section-title">Abstract</div>
            <div class="modal-section-content">${escapeHtml(paper.abstract || 'No abstract available.')}</div>
        </div>
        
        ${summaryHtml}
        
        ${paper.text_preview ? `
            <div class="modal-section">
                <div class="modal-section-title">Extracted Text Preview</div>
                <div class="modal-section-content" style="max-height: 200px; overflow-y: auto; font-size: 0.8rem;">${escapeHtml(paper.text_preview)}</div>
            </div>
        ` : ''}
        
        <div class="modal-section">
            <div class="modal-section-title">Links</div>
            <div class="modal-section-content">
                ${paper.pdf_url ? `<a href="${paper.pdf_url}" target="_blank">📄 Download PDF</a><br>` : ''}
                ${paper.url ? `<a href="${paper.url}" target="_blank">🔗 View on ${sourceLabel}</a><br>` : ''}
                ${paper.arxiv_id ? `<a href="https://arxiv.org/abs/${paper.arxiv_id}" target="_blank">📚 arXiv page</a>` : ''}
            </div>
        </div>
    `;

    paperModal.classList.add('visible');
}

modalClose.addEventListener('click', () => paperModal.classList.remove('visible'));
paperModal.addEventListener('click', (e) => {
    if (e.target === paperModal) paperModal.classList.remove('visible');
});

// =============================================
// Stats
// =============================================
function updateStats(stats) {
    if (!stats) return;
    $('#statTotal').textContent = stats.total || 0;
    $('#statArxiv').textContent = stats.arxiv || 0;
    $('#statSemantic').textContent = stats.semantic_scholar || 0;
    $('#statPdfs').textContent = stats.pdfs_downloaded || 0;
    $('#statSummaries').textContent = stats.summarized || 0;
    statsRow.style.display = 'flex';
}

// =============================================
// Pipeline Animation
// =============================================
function animatePipeline() {
    const steps = ['search', 'download', 'extract', 'summarize', 'store'];
    let stepIndex = 0;

    $$('.progress-steps .step').forEach(s => {
        s.classList.remove('active', 'done');
    });
    progressFill.style.width = '0%';

    const interval = setInterval(() => {
        if (stepIndex >= steps.length) {
            clearInterval(interval);
            return;
        }

        // Mark previous as done
        if (stepIndex > 0) {
            const prevStep = $(`.step[data-step="${steps[stepIndex - 1]}"]`);
            prevStep.classList.remove('active');
            prevStep.classList.add('done');
        }

        // Mark current as active
        const currentStep = $(`.step[data-step="${steps[stepIndex]}"]`);
        currentStep.classList.add('active');

        // Update progress
        progressFill.style.width = `${((stepIndex + 1) / steps.length) * 100}%`;

        stepIndex++;
    }, 2000);

    window._pipelineInterval = interval;
}

function completePipeline() {
    if (window._pipelineInterval) clearInterval(window._pipelineInterval);
    $$('.progress-steps .step').forEach(s => {
        s.classList.remove('active');
        s.classList.add('done');
    });
    progressFill.style.width = '100%';
}

// =============================================
// Web Scraper
// =============================================
scrapeBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) { showToast('Please enter a URL', 'error'); return; }

    scrapeBtn.classList.add('loading');
    scraperResults.style.display = 'none';

    try {
        const dynamic = $('#dynamicToggle').checked;
        const autoDetect = $('#autoDetect').checked;

        const response = await fetch('/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, dynamic, auto_detect: autoDetect }),
        });

        const data = await response.json();
        lastScrapeData = data;

        // Update status
        const isSuccess = data.success;
        const statusIcon = $('#statusIcon');
        statusIcon.className = `status-icon ${isSuccess ? 'success' : 'error'}`;
        $('#statusText').textContent = isSuccess ? 'Success' : 'Failed';
        $('#statusUrl').textContent = data.url || url;
        $('#scraperType').textContent = data.scraper_type || 'auto';
        const responseTime = data.metadata?.response_time;
        $('#responseTime').textContent = responseTime ? `${responseTime.toFixed(2)}s` : '-';

        // Update content
        $('#pageTitle').textContent = data.content?.title || 'No title';
        $('#pageText').textContent = data.content?.text || 'No text extracted';

        // Update links
        const linksGrid = $('#linksGrid');
        linksGrid.innerHTML = '';
        (data.content?.links || []).forEach(link => {
            const a = document.createElement('a');
            a.className = 'link-item';
            a.href = link;
            a.target = '_blank';
            a.textContent = link;
            linksGrid.appendChild(a);
        });

        // Update JSON
        $('#jsonOutput').textContent = JSON.stringify(data, null, 2);

        scraperResults.style.display = 'block';
        showToast(isSuccess ? 'Scraping complete!' : 'Scraping failed', isSuccess ? 'success' : 'error');
    } catch (err) {
        showToast(`Scrape failed: ${err.message}`, 'error');
    } finally {
        scrapeBtn.classList.remove('loading');
    }
});

// Content Tabs
$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        $$('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        $$('.tab-pane').forEach(p => p.classList.remove('active'));
        $(`.tab-pane[data-tab="${tab}"]`).classList.add('active');
    });
});

// Copy JSON
$('#copyBtn')?.addEventListener('click', () => {
    if (lastScrapeData) {
        navigator.clipboard.writeText(JSON.stringify(lastScrapeData, null, 2));
        showToast('Copied to clipboard!', 'success');
    }
});

// Clear buttons
clearResearchBtn?.addEventListener('click', () => { researchQuery.value = ''; });
clearBtn?.addEventListener('click', () => { urlInput.value = ''; });

// Enter key support
researchQuery?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchBtn.click();
});
urlInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') scrapeBtn.click();
});

// =============================================
// Utilities
// =============================================
function getSelectedSource() {
    const checked = document.querySelector('input[name="source"]:checked');
    return checked ? checked.value : 'both';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    toast.className = `toast visible ${type}`;
    setTimeout(() => { toast.classList.remove('visible'); }, 3000);
}

// =============================================
// Init — Load stats on page load
// =============================================
(async function init() {
    try {
        const res = await fetch('/research/stats');
        const stats = await res.json();
        if (stats.total_papers) {
            totalPapersEl.textContent = stats.total_papers;
        }
    } catch (e) {
        // Stats unavailable, that's fine
    }
})();
