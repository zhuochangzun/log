// ai-sales-advisor/frontend/config.js
const CONFIG = {
    apiBaseUrl: "http://localhost:8000",
    visitorId: localStorage.getItem('visitor_id') || generateVisitorId(),
};

function generateVisitorId() {
    const id = 'v_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('visitor_id', id);
    return id;
}

// 保存 visitorId 到 localStorage
localStorage.setItem('visitor_id', CONFIG.visitorId);