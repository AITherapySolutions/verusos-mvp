let currentFilter = null;

async function loadStats() {
    try {
        const response = await fetch('/dashboard/stats');
        const stats = await response.json();
        
        document.getElementById('pending-reviews').textContent = stats.pending_reviews;
        document.getElementById('overdue-reviews').textContent = stats.overdue_reviews;
        document.getElementById('avg-response').textContent = stats.average_response_time_minutes 
            ? `${stats.average_response_time_minutes}m` : 'N/A';
        document.getElementById('compliance-rate').textContent = stats.compliance_rate 
            ? `${stats.compliance_rate}%` : 'N/A';
        
        document.getElementById('tier-1-count').textContent = stats.tier_1_alerts;
        document.getElementById('tier-2-count').textContent = stats.tier_2_alerts;
        document.getElementById('tier-3-count').textContent = stats.tier_3_alerts;
        document.getElementById('tier-4-count').textContent = stats.tier_4_alerts;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadAlerts(tier = null, status = null) {
    try {
        let url = '/dashboard/alerts?limit=50';
        if (tier) url += `&tier=${tier}`;
        if (status) url += `&status=${status}`;
        
        const response = await fetch(url);
        const alerts = await response.json();
        
        const container = document.getElementById('alerts-container');
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="p-8 text-center text-gray-500">No alerts found</div>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-card p-4">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3 mb-2">
                            <span class="tier-badge tier-${alert.risk_tier}">
                                Tier ${alert.risk_tier}
                            </span>
                            <span class="font-medium">${alert.assessment_id}</span>
                            <span class="text-gray-500 text-sm">${alert.company_name}</span>
                            ${alert.is_overdue ? '<span class="overdue-indicator text-red-600 text-sm font-medium">OVERDUE</span>' : ''}
                        </div>
                        <p class="text-gray-600 text-sm mb-2">${alert.context_for_review || 'No context available'}</p>
                        <div class="flex items-center space-x-4 text-xs text-gray-500">
                            <span>Score: ${alert.risk_score}</span>
                            <span>Detected: ${new Date(alert.detected_at).toLocaleString()}</span>
                            ${alert.response_time_minutes ? `<span>Response: ${alert.response_time_minutes}m</span>` : '<span class="text-orange-600">Awaiting response</span>'}
                        </div>
                        <div class="mt-2">
                            ${alert.flags.suicide_ideation ? '<span class="flag-badge critical">Suicide Ideation</span>' : ''}
                            ${alert.flags.planning_language ? '<span class="flag-badge critical">Planning</span>' : ''}
                            ${alert.flags.isolation_markers ? '<span class="flag-badge">Isolation</span>' : ''}
                            ${(alert.flags.boundary_concerns || []).map(c => `<span class="flag-badge">${c}</span>`).join('')}
                        </div>
                    </div>
                    <div class="ml-4 flex flex-col items-end gap-3">
                        <button class="review-btn" 
                                onclick="openReviewModal('${alert.assessment_id}')"
                                ${alert.review_status ? 'disabled' : ''}>
                            ${alert.review_status ? '✅ Reviewed' : '📝 Review'}
                        </button>
                        ${alert.review_status ? 
                            `<span class="status-badge status-${alert.review_status}">
                                ${alert.review_status.charAt(0).toUpperCase() + alert.review_status.slice(1).replace(/_/g, ' ')}
                            </span>` 
                            : ''}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alerts-container').innerHTML = 
            '<div class="p-8 text-center text-red-500">Error loading alerts</div>';
    }
}

function filterAlerts(filter) {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-indigo-600', 'text-white');
        btn.classList.add('bg-gray-200');
    });
    
    event.target.classList.add('active', 'bg-indigo-600', 'text-white');
    event.target.classList.remove('bg-gray-200');
    
    if (filter === 'pending') {
        loadAlerts(null, 'pending');
    } else {
        loadAlerts(filter, null);
    }
}

// Alias for openReview - used in alert table
function openReviewModal(assessmentId) {
    return openReview(assessmentId);
}

async function openReview(assessmentId) {
    const modal = document.getElementById('review-modal');
    const content = document.getElementById('modal-content');
    
    modal.classList.remove('hidden');
    content.innerHTML = '<div class="text-center py-8">Loading...</div>';
    
    try {
        const response = await fetch(`/dashboard/alert/${assessmentId}`);
        const data = await response.json();
        
        content.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-semibold text-lg mb-3">Detection Details</h4>
                        <div class="bg-gray-50 p-4 rounded-lg space-y-2">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Assessment ID:</span>
                                <span class="font-medium">${data.detection.assessment_id}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Risk Score:</span>
                                <span class="font-bold text-lg">${data.detection.risk_score}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Tier:</span>
                                <span class="tier-badge tier-${data.detection.risk_tier}">${data.detection.tier_label}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">CMD-1 Score:</span>
                                <span>${data.detection.stanford_cmd1_score}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-semibold text-lg mb-3">Flags</h4>
                        <div class="bg-gray-50 p-4 rounded-lg space-y-2">
                            <div class="flex justify-between">
                                <span class="text-gray-500">Suicide Ideation:</span>
                                <span class="${data.detection.flags.suicide_ideation ? 'text-red-600 font-medium' : 'text-gray-400'}">${data.detection.flags.suicide_ideation ? 'YES' : 'No'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Planning Language:</span>
                                <span class="${data.detection.flags.planning_language ? 'text-red-600 font-medium' : 'text-gray-400'}">${data.detection.flags.planning_language ? 'YES' : 'No'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Isolation Markers:</span>
                                <span class="${data.detection.flags.isolation_markers ? 'text-orange-600 font-medium' : 'text-gray-400'}">${data.detection.flags.isolation_markers ? 'YES' : 'No'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-500">Temporal Pattern:</span>
                                <span>${data.detection.flags.temporal_pattern || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-semibold text-lg mb-3">Message Content</h4>
                    <div class="bg-red-50 border border-red-200 p-4 rounded-lg">
                        <p class="text-sm text-gray-500 mb-1">User Message:</p>
                        <p class="text-gray-800">${data.detection.user_message}</p>
                    </div>
                    ${data.detection.bot_message ? `
                    <div class="bg-blue-50 border border-blue-200 p-4 rounded-lg mt-3">
                        <p class="text-sm text-gray-500 mb-1">Bot Response:</p>
                        <p class="text-gray-800">${data.detection.bot_message}</p>
                    </div>
                    ` : ''}
                </div>
                
                <div>
                    <h4 class="font-semibold text-lg mb-3">Context for Review</h4>
                    <div class="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                        <p class="text-gray-800">${data.detection.context_for_review}</p>
                    </div>
                </div>
                
                ${data.company_response ? `
                <div>
                    <h4 class="font-semibold text-lg mb-3">Company Response</h4>
                    <div class="bg-green-50 border border-green-200 p-4 rounded-lg space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-500">Response Time:</span>
                            <span class="font-medium">${data.company_response.response_time_minutes} minutes</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">Crisis Resources Displayed:</span>
                            <span class="${data.company_response.crisis_resources_displayed ? 'text-green-600' : 'text-red-600'}">${data.company_response.crisis_resources_displayed ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">User Acknowledged:</span>
                            <span>${data.company_response.user_acknowledged_resources === null ? 'Unknown' : (data.company_response.user_acknowledged_resources ? 'Yes' : 'No')}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">Outcome:</span>
                            <span>${data.company_response.outcome_category || 'Not specified'}</span>
                        </div>
                        ${data.company_response.additional_notes ? `
                        <div class="mt-2 pt-2 border-t">
                            <p class="text-sm text-gray-500">Notes:</p>
                            <p>${data.company_response.additional_notes}</p>
                        </div>
                        ` : ''}
                    </div>
                </div>
                ` : `
                <div class="bg-orange-50 border border-orange-200 p-4 rounded-lg">
                    <p class="text-orange-700 font-medium">Company response not yet received</p>
                </div>
                `}
                
                <div class="border-t pt-6">
                    <h4 class="font-semibold text-lg mb-4">Tammy's Compliance Assessment</h4>
                    <form onsubmit="submitReview(event, '${data.detection.assessment_id}')" class="space-y-6">
                        <div>
                            <p class="text-sm font-medium text-gray-700 mb-3">Select Assessment Status:</p>
                            <div class="grid grid-cols-3 gap-3">
                                <label class="relative flex flex-col p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-green-400 transition-colors">
                                    <input type="radio" name="assessment" value="approved" class="sr-only assessment-radio" onchange="updateAssessmentStyle(this)">
                                    <span class="text-2xl mb-2">✅</span>
                                    <span class="font-semibold text-green-700">Compliant</span>
                                    <span class="text-xs text-gray-600">Company response is appropriate</span>
                                </label>
                                <label class="relative flex flex-col p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-orange-400 transition-colors">
                                    <input type="radio" name="assessment" value="revision_requested" class="sr-only assessment-radio" onchange="updateAssessmentStyle(this)">
                                    <span class="text-2xl mb-2">⚠️</span>
                                    <span class="font-semibold text-orange-700">Needs Follow-Up</span>
                                    <span class="text-xs text-gray-600">Request revision/more info</span>
                                </label>
                                <label class="relative flex flex-col p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-red-400 transition-colors">
                                    <input type="radio" name="assessment" value="escalated" class="sr-only assessment-radio" onchange="updateAssessmentStyle(this)">
                                    <span class="text-2xl mb-2">❌</span>
                                    <span class="font-semibold text-red-700">Non-Compliant</span>
                                    <span class="text-xs text-gray-600">Serious concerns or escalation</span>
                                </label>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Evaluation Checklist</label>
                            <div class="space-y-2 bg-gray-50 p-3 rounded-lg">
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" name="response_appropriate" class="rounded">
                                    <span class="text-sm">✓ Company response was appropriate</span>
                                </label>
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" name="resources_adequate" class="rounded">
                                    <span class="text-sm">✓ Crisis resources were adequate</span>
                                </label>
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" name="timing_acceptable" class="rounded">
                                    <span class="text-sm">✓ Response timing met deadline</span>
                                </label>
                                <label class="flex items-center space-x-2">
                                    <input type="checkbox" name="protocol_followed" class="rounded">
                                    <span class="text-sm">✓ Protocol was properly followed</span>
                                </label>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Compliance Notes</label>
                            <textarea name="reviewer_notes" rows="3" placeholder="Document your assessment findings..." class="w-full border rounded-lg p-3 text-sm"></textarea>
                        </div>
                        
                        <div class="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                            <p class="text-xs text-blue-800"><strong>Reviewer:</strong> Tammy | <strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                        </div>
                        
                        <div class="flex space-x-4">
                            <button type="submit" name="action" value="approved" class="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 font-medium transition-colors">
                                ✅ Mark Compliant
                            </button>
                            <button type="submit" name="action" value="revision_requested" class="flex-1 bg-orange-600 text-white py-3 px-4 rounded-lg hover:bg-orange-700 font-medium transition-colors">
                                ⚠️ Needs Follow-Up
                            </button>
                            <button type="submit" name="action" value="escalated" class="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 font-medium transition-colors">
                                ❌ Non-Compliant
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading alert details:', error);
        content.innerHTML = '<div class="text-center text-red-500 py-8">Error loading details</div>';
    }
}

async function submitReview(event, assessmentId) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const action = event.submitter.value;
    
    const reviewData = {
        detection_id: assessmentId,
        reviewer_name: "Tammy",
        status: action,
        response_appropriate: formData.get('response_appropriate') === 'on',
        resources_adequate: formData.get('resources_adequate') === 'on',
        timing_acceptable: formData.get('timing_acceptable') === 'on',
        protocol_followed: formData.get('protocol_followed') === 'on',
        reviewer_notes: formData.get('reviewer_notes')
    };
    
    try {
        const response = await fetch('/dashboard/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reviewData)
        });
        
        if (response.ok) {
            closeModal();
            refreshData();
            alert('Review submitted successfully');
        } else {
            alert('Error submitting review');
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        alert('Error submitting review');
    }
}

function closeModal() {
    document.getElementById('review-modal').classList.add('hidden');
}

function refreshData() {
    loadStats();
    loadAlerts();
}

document.addEventListener('DOMContentLoaded', () => {
    refreshData();
    setInterval(refreshData, 30000);
});

document.getElementById('review-modal').addEventListener('click', (e) => {
    if (e.target.id === 'review-modal') {
        closeModal();
    }
});

function updateAssessmentStyle(radio) {
    document.querySelectorAll('.assessment-radio').forEach(r => {
        r.parentElement.classList.remove('border-green-400', 'border-orange-400', 'border-red-400', 'bg-green-50', 'bg-orange-50', 'bg-red-50');
    });
    
    if (radio.checked) {
        const label = radio.parentElement;
        if (radio.value === 'approved') {
            label.classList.add('border-green-400', 'bg-green-50');
        } else if (radio.value === 'revision_requested') {
            label.classList.add('border-orange-400', 'bg-orange-50');
        } else if (radio.value === 'escalated') {
            label.classList.add('border-red-400', 'bg-red-50');
        }
    }
}

async function exportComplianceReport() {
    try {
        const response = await fetch('/dashboard/export-report');
        
        if (!response.ok) {
            alert('Error exporting report');
            return;
        }
        
        const blob = await response.blob();
        const element = document.createElement('a');
        element.href = URL.createObjectURL(blob);
        element.download = `verus-compliance-report-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
        
        alert('Compliance Report exported successfully!');
    } catch (error) {
        console.error('Error exporting report:', error);
        alert('Error exporting report');
    }
}

async function generateProtocolPage() {
    try {
        const response = await fetch('/dashboard/generate-protocol');
        const data = await response.json();
        
        if (!response.ok) {
            alert('Error generating protocol page: ' + data.detail);
            return;
        }
        
        const element = document.createElement('a');
        const file = new Blob([data.html], {type: 'text/html'});
        element.href = URL.createObjectURL(file);
        element.download = `verus-crisis-protocol-${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
        
        alert('Crisis Protocol Page generated and downloaded successfully!');
    } catch (error) {
        console.error('Error generating protocol page:', error);
        alert('Error generating protocol page');
    }
}

function openProtocolGenerator() {
    const modal = document.getElementById('protocolModal');
    modal.classList.add('active');
    generateProtocolPreview();
}

function closeProtocolModal() {
    const modal = document.getElementById('protocolModal');
    modal.classList.remove('active');
}

async function generateProtocolPreview() {
    try {
        const response = await fetch('/api/v1/protocol/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: 'Demo Company',
                company_id: 'demo',
                protocol_version: '1.0',
                contact_email: 'safety@example.com'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate protocol');
        }
        
        const data = await response.json();
        window.currentProtocol = data;
        
        document.getElementById('protocolPreview').textContent = 
            data.markdown.substring(0, 500) + '...';
        
        document.getElementById('downloadMarkdown').disabled = false;
        document.getElementById('downloadHTML').disabled = false;
    } catch (error) {
        console.error('Error generating protocol:', error);
        document.getElementById('protocolPreview').textContent = 'Error generating protocol';
    }
}

function downloadMarkdown() {
    if (!window.currentProtocol) return;
    
    const blob = new Blob([window.currentProtocol.markdown], {type: 'text/markdown'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crisis-protocol-${window.currentProtocol.company_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

function downloadHTML() {
    if (!window.currentProtocol) return;
    
    const blob = new Blob([window.currentProtocol.html], {type: 'text/html'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crisis-protocol-${window.currentProtocol.company_id}.html`;
    a.click();
    URL.revokeObjectURL(url);
}

// Export functions
async function exportDetailed() {
    try {
        const response = await fetch('/api/v1/export/annual-report?export_type=detailed', {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `verus-detailed-report-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting detailed report');
    }
}

async function exportSummary() {
    try {
        const response = await fetch('/api/v1/export/annual-report?export_type=summary', {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `verus-summary-report-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting summary report');
    }
}

function openCustomExportModal() {
    document.getElementById('customExportModal').classList.add('active');
}

function closeCustomExportModal() {
    document.getElementById('customExportModal').classList.remove('active');
}

async function submitCustomExport() {
    try {
        const exportType = document.getElementById('exportTypeSelect').value;
        const companyId = document.getElementById('exportCompanyId').value || null;
        const startDate = document.getElementById('exportStartDate').value || null;
        const endDate = document.getElementById('exportEndDate').value || null;
        
        let url = `/api/v1/export/annual-report?export_type=${exportType}`;
        if (companyId) url += `&company_id=${companyId}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        
        const response = await fetch(url, { method: 'POST' });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const urlObj = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = urlObj;
        a.download = `verus-export-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(urlObj);
        document.body.removeChild(a);
        
        closeCustomExportModal();
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting custom report');
    }
}

window.onclick = function(event) {
    const protocolModal = document.getElementById('protocolModal');
    const exportModal = document.getElementById('customExportModal');
    
    if (event.target == protocolModal) {
        closeProtocolModal();
    }
    if (event.target == exportModal) {
        closeCustomExportModal();
    }
}
