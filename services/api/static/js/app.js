/**
 * RAF Chatbot - Main Application Script
 * 
 * Features:
 * - Real-time chat interface
 * - System metrics tracking
 * - Health status monitoring
 * - Auto-refresh metrics
 */

// ============================================
// CONFIGURATION
// ============================================

const API_BASE_URL = window.location.origin;
const METRICS_UPDATE_INTERVAL = 5000; // 5 seconds

// ============================================
// DOM ELEMENTS
// ============================================

const chatMessages = document.getElementById('chatMessages');
const queryForm = document.getElementById('queryForm');
const queryInput = document.getElementById('queryInput');
const sendButton = document.getElementById('sendButton');
const loadingOverlay = document.getElementById('loadingOverlay');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const refreshMetricsBtn = document.getElementById('refreshMetricsBtn');
const clearChatBtn = document.getElementById('clearChatBtn');

// ============================================
// STATE
// ============================================

let isLoading = false;
let metricsUpdateInterval = null;
let messageCount = 0;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 RAF Chatbot initialized');
    initializeApp();
});

function initializeApp() {
    attachEventListeners();
    checkSystemStatus();
    updateMetrics();
    startMetricsAutoUpdate();
    queryInput.focus();
}

// ============================================
// EVENT LISTENERS
// ============================================

function attachEventListeners() {
    queryForm.addEventListener('submit', handleQuerySubmit);
    refreshMetricsBtn.addEventListener('click', updateMetrics);
    clearChatBtn.addEventListener('click', clearChat);
    
    queryInput.addEventListener('input', () => {
        sendButton.disabled = !queryInput.value.trim();
    });
}

// ============================================
// QUERY HANDLING
// ============================================

async function handleQuerySubmit(e) {
    e.preventDefault();
    
    const question = queryInput.value.trim();
    if (!question || isLoading) return;
    
    // Add user message to chat
    addMessageToChat(question, 'user');
    queryInput.value = '';
    queryInput.focus();
    
    // Show loading state
    setLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/query/simple`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: question,
                rag_id: 'default',
                top_k: 5,
                score_threshold: 0.0
            }),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Extract response from data
        const assistantMessage = data.answer || 'No response generated';
        const sources = data.sources || [];
        
        // Add assistant response
        addMessageToChat(assistantMessage, 'assistant', sources);
        
        // Update metrics after successful query
        setTimeout(updateMetrics, 500);
        
    } catch (error) {
        console.error('❌ Query error:', error);
        addMessageToChat(
            `❌ Error: ${error.message}. Please try again.`,
            'assistant'
        );
    } finally {
        setLoading(false);
        queryInput.focus();
    }
}

// ============================================
// CHAT MANAGEMENT
// ============================================

function addMessageToChat(text, sender, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const messageContent = document.createElement('p');
    messageContent.textContent = text;
    messageDiv.appendChild(messageContent);
    
    // Add sources metadata if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-metadata';
        const sourceText = Array.isArray(sources) ? sources.join(', ') : sources;
        sourcesDiv.innerHTML = `📚 <strong>Sources:</strong> ${escapeHtml(sourceText)}`;
        messageDiv.appendChild(sourcesDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 0);
    
    messageCount++;
}

function clearChat() {
    chatMessages.innerHTML = '';
    messageCount = 0;
    addWelcomeMessage();
    queryInput.focus();
}

function addWelcomeMessage() {
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message system-message';
    welcomeDiv.innerHTML = `
        <p>👋 Welcome to RAF Chatbot! Ask me anything and I'll search through documents to find the best answer.</p>
    `;
    chatMessages.appendChild(welcomeDiv);
}

// ============================================
// METRICS
// ============================================

async function updateMetrics() {
    try {
        const response = await fetch(`${API_BASE_URL}/metrics`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        
        const metrics = await response.json();
        
        // Update metric displays
        updateMetricDisplay('metricRequests', formatNumber(metrics.requests_total));
        updateMetricDisplay('metricErrors', formatNumber(metrics.errors_total));
        updateMetricDisplay('metricCacheHits', formatNumber(metrics.cache_hits_total));
        updateMetricDisplay('metricRateLimited', formatNumber(metrics.rate_limited_total));
        updateMetricDisplay('metricAvgLatency', 
            metrics.avg_latency_ms.toFixed(2) + ' ms');
        updateMetricDisplay('metricP95Latency', 
            metrics.p95_latency_ms.toFixed(2) + ' ms');
        
    } catch (error) {
        console.error('Error updating metrics:', error);
    }
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function updateMetricDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function startMetricsAutoUpdate() {
    metricsUpdateInterval = setInterval(() => {
        updateMetrics();
    }, METRICS_UPDATE_INTERVAL);
}

function stopMetricsAutoUpdate() {
    if (metricsUpdateInterval) {
        clearInterval(metricsUpdateInterval);
        metricsUpdateInterval = null;
    }
}

// ============================================
// SYSTEM STATUS
// ============================================

async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        
        if (response.ok) {
            updateStatusIndicator(true);
            return true;
        } else {
            updateStatusIndicator(false);
            return false;
        }
    } catch (error) {
        console.error('⚠️ Health check failed:', error);
        updateStatusIndicator(false);
        return false;
    }
}

function updateStatusIndicator(online) {
    if (online) {
        statusDot.classList.add('online');
        statusDot.classList.remove('offline');
        statusText.textContent = 'System Online';
        queryInput.disabled = false;
        sendButton.disabled = !queryInput.value.trim();
    } else {
        statusDot.classList.remove('online');
        statusDot.classList.add('offline');
        statusText.textContent = 'System Offline';
        queryInput.disabled = true;
        sendButton.disabled = true;
    }
}

// ============================================
// UI STATE
// ============================================

function setLoading(loading) {
    isLoading = loading;
    
    if (loading) {
        loadingOverlay.classList.add('show');
        sendButton.disabled = true;
        queryInput.disabled = true;
    } else {
        loadingOverlay.classList.remove('show');
        sendButton.disabled = !queryInput.value.trim();
        queryInput.disabled = false;
    }
}

// ============================================
// UTILITIES
// ============================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// CLEANUP
// ============================================

window.addEventListener('beforeunload', () => {
    stopMetricsAutoUpdate();
});

// Periodically check system status
setInterval(checkSystemStatus, 15000); // Every 15 seconds