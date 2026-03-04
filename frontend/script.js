/**
 * AI Web Scraper - Frontend JavaScript
 */

const API_BASE = 'http://localhost:8000';

// DOM Elements
const urlInput = document.getElementById('urlInput');
const clearBtn = document.getElementById('clearBtn');
const dynamicToggle = document.getElementById('dynamicToggle');
const autoDetect = document.getElementById('autoDetect');
const scrapeBtn = document.getElementById('scrapeBtn');
const resultsSection = document.getElementById('resultsSection');
const statusCard = document.getElementById('statusCard');
const statusIcon = document.getElementById('statusIcon');
const statusText = document.getElementById('statusText');
const statusUrl = document.getElementById('statusUrl');
const scraperType = document.getElementById('scraperType');
const responseTime = document.getElementById('responseTime');
const pageTitle = document.getElementById('pageTitle');
const pageText = document.getElementById('pageText');
const linksGrid = document.getElementById('linksGrid');
const jsonOutput = document.getElementById('jsonOutput');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const totalScrapes = document.getElementById('totalScrapes');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

// State
let currentData = null;
let scrapeCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setupEventListeners();
});

function setupEventListeners() {
    // Clear button
    clearBtn.addEventListener('click', () => {
        urlInput.value = '';
        urlInput.focus();
    });

    // Enter key to scrape
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            scrapeWebsite();
        }
    });

    // Scrape button
    scrapeBtn.addEventListener('click', scrapeWebsite);

    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });

    // Copy button
    copyBtn.addEventListener('click', copyToClipboard);

    // Download button
    downloadBtn.addEventListener('click', downloadJSON);

    // Auto-detect toggle
    autoDetect.addEventListener('change', () => {
        if (autoDetect.checked) {
            dynamicToggle.checked = false;
        }
    });

    dynamicToggle.addEventListener('change', () => {
        if (dynamicToggle.checked) {
            autoDetect.checked = false;
        }
    });
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (response.ok) {
            const stats = await response.json();
            scrapeCount = stats.total_scrapes || stats.total || 0;
            totalScrapes.querySelector('.stat-value').textContent = scrapeCount;
        }
    } catch (error) {
        console.log('Could not load stats:', error);
    }
}

async function scrapeWebsite() {
    const url = urlInput.value.trim();

    if (!url) {
        showToast('Please enter a URL to scrape');
        urlInput.focus();
        return;
    }

    if (!isValidUrl(url)) {
        showToast('Please enter a valid URL (e.g., https://example.com)');
        urlInput.focus();
        return;
    }

    // Set loading state
    scrapeBtn.classList.add('loading');
    scrapeBtn.disabled = true;

    try {
        const params = new URLSearchParams({
            url: url,
            dynamic: dynamicToggle.checked,
            auto_detect: autoDetect.checked
        });

        const response = await fetch(`${API_BASE}/scrape?${params}`);
        const data = await response.json();

        if (response.ok && data.success !== false) {
            currentData = data;
            displayResults(data);
            scrapeCount++;
            totalScrapes.querySelector('.stat-value').textContent = scrapeCount;
            showToast('✓ Website scraped successfully!');
        } else {
            const errorMsg = data.detail || data.error || 'Failed to scrape website';
            showError(url, errorMsg);
            showToast('✗ Scraping failed');
        }
    } catch (error) {
        console.error('Scrape error:', error);
        showError(url, error.message || 'Network error occurred');
        showToast('✗ Connection error');
    } finally {
        scrapeBtn.classList.remove('loading');
        scrapeBtn.disabled = false;
    }
}

function displayResults(data) {
    resultsSection.classList.add('visible');

    // Status
    statusIcon.className = 'status-icon success';
    statusIcon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
    `;
    statusText.textContent = 'Success';
    statusUrl.textContent = data.url;

    // Metadata
    scraperType.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
        </svg>
        ${data.scraper_type || 'auto'}
    `;

    const respTime = data.metadata?.response_time || 0;
    responseTime.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>
        ${respTime.toFixed(2)}s
    `;

    // Content
    pageTitle.textContent = data.content?.title || 'No title found';
    pageText.textContent = data.content?.text || 'No text content extracted';

    // Links
    const links = data.content?.links || [];
    linksGrid.innerHTML = links.length > 0
        ? links.slice(0, 50).map(link => `
            <a href="${escapeHtml(link)}" target="_blank" rel="noopener" class="link-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                ${escapeHtml(link)}
            </a>
        `).join('')
        : '<p class="no-links" style="color: var(--text-muted); padding: 1rem;">No links found</p>';

    // JSON
    jsonOutput.textContent = JSON.stringify(data, null, 2);

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(url, errorMessage) {
    resultsSection.classList.add('visible');

    statusIcon.className = 'status-icon error';
    statusIcon.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
    `;
    statusText.textContent = 'Error';
    statusUrl.textContent = url;

    scraperType.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
        </svg>
        --
    `;
    responseTime.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
        </svg>
        --
    `;

    pageTitle.textContent = 'Scraping Failed';
    pageText.textContent = errorMessage;
    linksGrid.innerHTML = '';
    jsonOutput.textContent = JSON.stringify({ error: errorMessage }, null, 2);

    currentData = { error: errorMessage };

    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function switchTab(tabName) {
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    tabPanes.forEach(pane => {
        pane.classList.toggle('active', pane.dataset.tab === tabName);
    });
}

async function copyToClipboard() {
    if (!currentData) return;

    try {
        await navigator.clipboard.writeText(JSON.stringify(currentData, null, 2));
        showToast('Copied to clipboard!');
    } catch (error) {
        showToast('Failed to copy');
    }
}

function downloadJSON() {
    if (!currentData) return;

    const blob = new Blob([JSON.stringify(currentData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scraped_data_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Downloaded!');
}

function showToast(message) {
    toastMessage.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
        return false;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
