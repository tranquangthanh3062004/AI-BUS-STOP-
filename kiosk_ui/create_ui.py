import os

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Trạm Xe Buýt Thông Minh - Kiosk Kính Mờ</title>
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='6' fill='%235b8cff'/%3E%3Crect x='5' y='6' width='14' height='9' rx='2' fill='white'/%3E%3Ccircle cx='8.5' cy='17' r='1.6' fill='white'/%3E%3Ccircle cx='15.5' cy='17' r='1.6' fill='white'/%3E%3C/svg%3E">

    <!-- Local Offline Fonts -->
    <link href="static/fonts/fonts.css" rel="stylesheet">

    <!-- Leaflet Interactive GIS Map CSS -->
    <link rel="stylesheet" href="static/libs/leaflet.css" />
    <link rel="stylesheet" href="static/libs/leaflet-routing-machine.css" />

    <style>
        :root {
            /* Glassmorphism Dark Theme */
            --glass-bg: rgba(18, 18, 22, 0.75);
            --glass-bg-hover: rgba(30, 30, 35, 0.85);
            --glass-border: rgba(255, 255, 255, 0.12);
            --glass-shadow: 0 24px 60px -12px rgba(0, 0, 0, 0.6);
            --glass-blur: blur(40px);

            /* Accents */
            --accent: #00d2ff;
            --accent-2: #3a7bd5;
            --accent-grad: linear-gradient(135deg, var(--accent), var(--accent-2));
            
            --success: #22c58b;
            --warning: #f2a93c;
            --danger: #f2555b;

            /* Text */
            --text-1: #ffffff;
            --text-2: #a0a0ab;
            --text-3: #757580;

            --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
            --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body, html {
            width: 100%;
            height: 100%;
            overflow: hidden;
            font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
            background: #000;
            color: var(--text-1);
        }

        /* ---------------------------------------------------- */
        /* MAP LAYER */
        /* ---------------------------------------------------- */
        #bus-map {
            position: absolute;
            inset: 0;
            z-index: 1;
            /* Tweak leaflet default colors for better dark integration if needed */
        }
        
        .leaflet-control-zoom {
            display: none !important; /* Hide default zoom controls to keep UI clean */
        }

        /* ---------------------------------------------------- */
        /* UI LAYER OVERLAY */
        /* ---------------------------------------------------- */
        .ui-layer {
            position: absolute;
            inset: 0;
            z-index: 10;
            pointer-events: none; /* Let map receive drags/clicks */
            display: flex;
            flex-direction: column;
            padding: 32px;
        }

        /* Utility for interactive elements */
        .interactive {
            pointer-events: auto;
        }

        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            box-shadow: var(--glass-shadow);
        }

        /* ---------------------------------------------------- */
        /* HEADER (Top Bar) */
        /* ---------------------------------------------------- */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 28px;
            border-radius: 100px;
            margin-bottom: 24px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .brand-icon {
            background: var(--accent-grad);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 20px rgba(0, 210, 255, 0.4);
            color: #000;
        }

        .brand-text h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        
        .brand-text p {
            font-size: 0.85rem;
            color: var(--text-2);
            margin-top: 2px;
        }

        .header-controls {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .pill {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            border-radius: 100px;
            font-size: 0.95rem;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-1);
            transition: all 0.3s var(--ease-out);
            cursor: pointer;
        }

        .pill:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .pill.clock-display {
            font-family: 'JetBrains Mono', monospace;
            cursor: default;
        }

        .pill.online .status-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 12px var(--success);
        }

        /* ---------------------------------------------------- */
        /* MAIN WORKSPACE */
        /* ---------------------------------------------------- */
        .workspace {
            display: flex;
            flex: 1;
            gap: 24px;
            position: relative;
            min-height: 0;
        }

        /* ---------------------------------------------------- */
        /* LEFT CHAT SIDE-SHEET */
        /* ---------------------------------------------------- */
        .chat-sheet {
            width: 440px;
            border-radius: 32px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            animation: slideInLeft 0.6s var(--ease-out);
        }

        @keyframes slideInLeft {
            from { transform: translateX(-40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .chat-header {
            padding: 24px;
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header h2 {
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .clear-btn {
            background: none; border: none; color: var(--text-2); cursor: pointer;
            font-size: 0.85rem; display: flex; align-items: center; gap: 6px;
            transition: color 0.2s;
        }
        .clear-btn:hover { color: var(--danger); }

        .chat-history {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            scroll-behavior: smooth;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        
        /* Custom Scrollbar */
        .chat-history::-webkit-scrollbar { width: 6px; }
        .chat-history::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }

        .empty-state {
            margin: auto;
            text-align: center;
            color: var(--text-2);
            max-width: 80%;
        }

        .empty-state svg {
            width: 64px; height: 64px;
            opacity: 0.5;
            margin-bottom: 16px;
        }

        .empty-state h3 {
            color: var(--text-1);
            font-size: 1.2rem;
            margin-bottom: 8px;
        }

        .empty-state p {
            font-size: 0.95rem;
            line-height: 1.5;
        }

        /* Chat Bubbles */
        .msg-row {
            display: flex;
            flex-direction: column;
            gap: 8px;
            animation: popIn 0.4s var(--ease-out) both;
        }
        
        @keyframes popIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg-row.user {
            align-items: flex-end;
        }
        
        .msg-row.ai {
            align-items: flex-start;
        }

        .msg-name {
            font-size: 0.8rem;
            color: var(--text-3);
            margin: 0 12px;
        }

        .msg-bubble {
            padding: 16px 20px;
            font-size: 1rem;
            line-height: 1.5;
            max-width: 90%;
            word-wrap: break-word;
        }

        .msg-row.user .msg-bubble {
            background: var(--accent-grad);
            color: #000;
            border-radius: 24px 24px 4px 24px;
            font-weight: 500;
        }

        .msg-row.ai .msg-bubble {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--glass-border);
            border-radius: 24px 24px 24px 4px;
        }

        /* Route Cards inside Chat */
        .routes-grid {
            margin-top: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .route-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--glass-border);
            border-left: 4px solid var(--accent);
            border-radius: 16px;
            padding: 16px;
            cursor: pointer;
            transition: transform 0.2s, background 0.2s;
        }

        .route-card:hover {
            background: rgba(255, 255, 255, 0.05);
            transform: scale(1.02);
        }

        .route-card .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .route-badge {
            background: var(--accent);
            color: #000;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.85rem;
        }

        .fare-badge {
            color: var(--success);
            font-weight: 600;
            font-size: 0.9rem;
        }

        .route-card .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 12px;
        }

        .row-icon {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: var(--text-2);
            margin-bottom: 6px;
        }

        .msg-meta {
            margin-top: 12px;
            font-size: 0.75rem;
            color: var(--text-3);
            display: flex;
            gap: 12px;
        }

        /* Input Bar */
        .chat-input-bar {
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid var(--glass-border);
            display: flex;
            gap: 12px;
        }

        .text-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            border-radius: 100px;
            padding: 0 20px;
            color: #fff;
            font-size: 1rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .text-input:focus { border-color: var(--accent); }

        .send-button {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background: var(--text-1);
            color: #000;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        .send-button:hover { transform: scale(1.05); }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        /* ---------------------------------------------------- */
        /* RIGHT SIDE PRESETS */
        /* ---------------------------------------------------- */
        .presets-panel {
            position: absolute;
            right: 0;
            top: 0;
            width: 280px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            animation: slideInRight 0.6s var(--ease-out);
        }

        @keyframes slideInRight {
            from { transform: translateX(40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .preset-pill {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            padding: 16px;
            border-radius: 20px;
            color: var(--text-1);
            text-align: left;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }

        .preset-pill:hover {
            background: var(--glass-bg-hover);
            transform: translateX(-5px);
            border-color: rgba(255,255,255,0.2);
        }

        .preset-pill svg { color: var(--accent); }
        .preset-pill .title { font-weight: 500; font-size: 0.95rem; }
        .preset-pill .tag { font-size: 0.75rem; color: var(--text-3); margin-top: 4px; }

        /* ---------------------------------------------------- */
        /* FLOATING VOICE FAB (Bottom Center) */
        /* ---------------------------------------------------- */
        .voice-fab-container {
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            z-index: 100;
        }

        .mic-fab {
            width: 88px;
            height: 88px;
            border-radius: 50%;
            border: none;
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            color: var(--accent);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 16px 40px rgba(0,0,0,0.5);
            transition: all 0.4s var(--ease-out);
            position: relative;
        }
        
        .mic-fab svg { width: 36px; height: 36px; transition: transform 0.3s; }

        .mic-fab:hover {
            transform: scale(1.05);
            background: var(--glass-bg-hover);
        }

        .mic-fab.listening {
            background: var(--accent-grad);
            color: #000;
            border: none;
            animation: pulse-ring 2s infinite;
        }
        
        .mic-fab.listening svg { transform: scale(1.1); }

        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0.6); }
            70% { box-shadow: 0 0 0 30px rgba(0, 210, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0); }
        }

        .voice-status {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            padding: 8px 24px;
            border-radius: 100px;
            font-size: 0.95rem;
            font-weight: 500;
            border: 1px solid var(--glass-border);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s;
        }
        
        .mic-fab:hover + .voice-status, .mic-fab.listening + .voice-status {
            opacity: 1;
            transform: translateY(0);
        }

        /* ---------------------------------------------------- */
        /* ROUTE LABEL (Top Center Overlay) */
        /* ---------------------------------------------------- */
        .route-label-overlay {
            position: absolute;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            padding: 12px 32px;
            border-radius: 100px;
            border: 1px solid var(--glass-border);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .route-label-overlay.active { opacity: 1; }

        /* ---------------------------------------------------- */
        /* TOASTS */
        /* ---------------------------------------------------- */
        .toast-container {
            position: fixed;
            bottom: 40px;
            right: 40px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        }
        
        .toast {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            color: #fff;
            padding: 16px 24px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
            animation: slideInRight 0.4s var(--ease-out);
        }

    </style>
</head>
<body>
    <!-- Map Background Layer -->
    <div id="bus-map"></div>

    <!-- UI Overlay Layer -->
    <div class="ui-layer">
        
        <!-- Top Header -->
        <header class="glass-panel interactive">
            <div class="brand">
                <div class="brand-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"></path><circle cx="7" cy="17" r="2"></circle><path d="M9 17h6"></path><circle cx="17" cy="17" r="2"></circle></svg>
                </div>
                <div class="brand-text">
                    <h1>Trạm Xe Buýt Thông Minh</h1>
                    <p>Được hỗ trợ bởi AI Edge</p>
                </div>
            </div>
            
            <div class="header-controls">
                <div class="pill interactive" id="speaker-btn" onclick="toggleSpeaker()">
                    <svg id="speaker-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>
                    <span id="speaker-label">Giọng đọc Bật</span>
                </div>
                <div class="pill online">
                    <span class="status-dot"></span>
                    <span>HỆ THỐNG ONLINE</span>
                </div>
                <div class="pill clock-display" id="live-clock">12:00</div>
            </div>
        </header>

        <!-- Dynamic Route Label over Map -->
        <div id="active-route-overlay" class="route-label-overlay interactive">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6.5 9 4l6 2.5 6-2.5v15l-6 2.5L9 19l-6 2.5Z"></path><path d="M9 4v15"></path><path d="M15 6.5v15"></path></svg>
            <span id="active-route-label">Bản đồ lộ trình</span>
        </div>

        <div class="workspace">
            
            <!-- Left Side-Sheet: Chat Panel -->
            <div class="chat-sheet glass-panel interactive">
                <div class="chat-header">
                    <h2>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.5 8.5 0 0 1-12.7 7.4L4 20l1.2-4.2A8.5 8.5 0 1 1 21 11.5Z"></path></svg>
                        Trợ lý AI
                    </h2>
                    <button class="clear-btn" onclick="clearChat()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        Xóa Chat
                    </button>
                </div>
                
                <div class="chat-history" id="chat-history">
                    <div class="empty-state" id="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
                        <h3>Xin chào!</h3>
                        <p>Bạn muốn đi đâu hôm nay? Hãy chạm vào Micro bên dưới để nói, hoặc chọn câu hỏi mẫu bên phải.</p>
                    </div>
                </div>

                <div class="chat-input-bar">
                    <input type="text" class="text-input" id="user-input" placeholder="Nhập câu hỏi..." onkeydown="if(event.key==='Enter') sendMessage()">
                    <button class="send-button" id="send-btn" onclick="sendMessage()">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </button>
                </div>
            </div>

            <!-- Right Area: Quick Presets (Floating) -->
            <div class="presets-panel interactive">
                <div class="preset-pill" onclick="sendPreset('Đi từ Mỹ Đình đến Bách Khoa bằng xe buýt nào?')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path></svg>
                    <div>
                        <div class="title">Mỹ Đình ➔ Bách Khoa</div>
                        <div class="tag">Tuyến thẳng phổ biến</div>
                    </div>
                </div>
                <div class="preset-pill" onclick="sendPreset('Xe buýt nào đi qua Hồ Gươm?')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    <div>
                        <div class="title">Tuyến qua Hồ Gươm</div>
                        <div class="tag">Địa danh du lịch</div>
                    </div>
                </div>
                <div class="preset-pill" onclick="sendPreset('Bảng giá vé xe buýt và vé tháng?')">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M3 10h18"></path><path d="M8 14h.01"></path></svg>
                    <div>
                        <div class="title">Giá vé & Vé tháng</div>
                        <div class="tag">Hỏi quy định chung</div>
                    </div>
                </div>
            </div>

        </div> <!-- end workspace -->

        <!-- Bottom Center FAB Voice -->
        <div class="voice-fab-container interactive">
            <button class="mic-fab" id="mic-btn" onclick="toggleVoiceRecording()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0"></path><path d="M12 18v3"></path></svg>
            </button>
            <div class="voice-status" id="voice-status">Chạm để nói</div>
        </div>

    </div>

    <!-- Toast Notification Layer -->
    <div class="toast-container" id="toast-container"></div>

    <!-- Logic JS -->
    <script src="static/libs/leaflet.js"></script>
    <script src="static/libs/leaflet-routing-machine.js"></script>

    <script>
        // Core Logic (Re-implemented with same function signatures but UI updates)
        let isListening = false;
        let speakerEnabled = true;
        let recognition = null;
        let map = null;
        let routePolyline = null;
        let routingControl = null;
        let mapMarkers = [];

        window.networkMode = 'ONLINE'; // Always online

        const ACCENT_COLOR = '#00d2ff';
        const ROUTE_PALETTE = ['#00d2ff', '#22c58b', '#f2a93c', '#8b6bff', '#f2555b', '#e11d48'];

        function routeColor(id) {
            let hash = 0;
            for (const ch of String(id)) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
            return ROUTE_PALETTE[hash % ROUTE_PALETTE.length];
        }

        const STOPS_GEO = {
            "Mỹ Đình": [21.0285, 105.7782],
            "Cầu Giấy": [21.0362, 105.8015],
            "Bách Khoa": [21.0055, 105.8430],
            "Hồ Gươm": [21.0285, 105.8542],
            "Yên Nghĩa": [20.9575, 105.7485],
            "Giáp Bát": [20.9815, 105.8415],
            "Ga Cát Linh": [21.0275, 105.8285]
        };

        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `<span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(20px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function initMap() {
            if (typeof L === 'undefined') return;
            map = L.map('bus-map', { zoomControl: false, attributionControl: false }).setView([21.0285, 105.8042], 12);
            
            // High-quality Google Maps layer
            L.tileLayer('http://mt0.google.com/vt/lyrs=m&hl=vi&x={x}&y={y}&z={z}', {
                maxZoom: 18
            }).addTo(map);

            // Hide attribution entirely for clean glass UI
        }

        async function getCoords(name) {
            if (STOPS_GEO[name]) return STOPS_GEO[name];
            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(name + " Hà Nội")}&format=json&limit=1`);
                const data = await res.json();
                if (data && data.length > 0) return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
            } catch (e) { }
            return null;
        }

        async function drawRouteOnMap(originName, destName, itineraryStr = null) {
            if (!map) return;
            if (routePolyline) { map.removeLayer(routePolyline); routePolyline = null; }
            if (routingControl) { map.removeControl(routingControl); routingControl = null; }

            const labelOverlay = document.getElementById('active-route-overlay');
            const labelEl = document.getElementById('active-route-label');
            labelOverlay.classList.add('active');
            labelEl.innerText = `Đang phân tích lộ trình...`;

            let startCoords = await getCoords(originName) || STOPS_GEO["Mỹ Đình"];
            let endCoords = await getCoords(destName) || STOPS_GEO["Bách Khoa"];
            
            let waypoints = [L.latLng(startCoords[0], startCoords[1])];

            if (itineraryStr) {
                const stops = itineraryStr.split(/[-<>]/).map(s => s.trim()).filter(s => s.length > 2);
                if (stops.length > 3) {
                    const m1 = await getCoords(stops[Math.floor(stops.length/3)]);
                    if (m1) waypoints.push(L.latLng(m1[0], m1[1]));
                    const m2 = await getCoords(stops[Math.floor(stops.length*2/3)]);
                    if (m2) waypoints.push(L.latLng(m2[0], m2[1]));
                }
            }
            waypoints.push(L.latLng(endCoords[0], endCoords[1]));
            
            drawShortestPath(waypoints, originName, destName, labelEl);
        }

        function drawShortestPath(waypoints, originName, destName, labelEl) {
            mapMarkers.forEach(m => map.removeLayer(m));
            mapMarkers = [];
            let totalDistance = 0;
            
            waypoints.forEach((wp, index) => {
                let title = index === 0 ? originName : (index === waypoints.length-1 ? destName : "Trạm trung gian");
                const marker = L.marker(wp).addTo(map).bindPopup(`<b>${title}</b>`);
                mapMarkers.push(marker);
                if (index > 0) totalDistance += waypoints[index - 1].distanceTo(wp);
            });
            
            routePolyline = L.polyline(waypoints, { color: ACCENT_COLOR, weight: 6, opacity: 0.9, dashArray: '10, 15' }).addTo(map);
            map.fitBounds(routePolyline.getBounds(), { padding: [100, 100] });
            
            if (labelEl) {
                const distanceKm = (totalDistance / 1000).toFixed(1);
                labelEl.innerText = `${originName} ➔ ${destName} (${distanceKm} km)`;
            }
        }

        window.onload = function() {
            initMap();
            showToast("Hệ thống trực tuyến đã sẵn sàng", "success");
        };

        // TTS & STT
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'vi-VN';
            recognition.onresult = (e) => {
                document.getElementById('user-input').value = e.results[0][0].transcript;
                sendMessage();
                stopVoiceRecording();
            };
            recognition.onerror = () => { stopVoiceRecording(); showToast("Lỗi nhận diện giọng nói", "error"); };
            recognition.onend = stopVoiceRecording;
        }

        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString('vi-VN', {hour:'2-digit', minute:'2-digit'}); }, 1000);

        function toggleSpeaker() {
            speakerEnabled = !speakerEnabled;
            const icon = document.getElementById('speaker-icon');
            const label = document.getElementById('speaker-label');
            if (speakerEnabled) {
                icon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>';
                label.innerText = 'Giọng đọc Bật';
                showToast("Đã bật giọng nói", "success");
            } else {
                icon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line>';
                label.innerText = 'Đã tắt tiếng';
                window.speechSynthesis.cancel();
                showToast("Đã tắt giọng nói", "info");
            }
        }

        function toggleVoiceRecording() {
            if (!recognition) return showToast("Trình duyệt không hỗ trợ Mic", "error");
            const micBtn = document.getElementById('mic-btn');
            const status = document.getElementById('voice-status');
            if (!isListening) {
                isListening = true;
                micBtn.classList.add('listening');
                status.innerText = "Đang lắng nghe...";
                recognition.start();
            } else {
                stopVoiceRecording();
            }
        }

        function stopVoiceRecording() {
            isListening = false;
            document.getElementById('mic-btn').classList.remove('listening');
            document.getElementById('voice-status').innerText = "Chạm để nói";
            if (recognition) recognition.stop();
        }

        function speakVietnamese(text) {
            if (!speakerEnabled || !window.speechSynthesis) return;
            window.speechSynthesis.cancel();
            const cleanText = text.replace(/[*#\-]/g, ' ').slice(0, 250);
            const utt = new SpeechSynthesisUtterance(cleanText);
            utt.lang = 'vi-VN';
            window.speechSynthesis.speak(utt);
        }

        function sendPreset(text) {
            document.getElementById('user-input').value = text;
            sendMessage();
        }

        function clearChat() {
            document.getElementById('chat-history').innerHTML = `
                <div class="empty-state" id="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
                    <h3>Xin chào!</h3>
                    <p>Bạn muốn đi đâu hôm nay? Hãy chạm vào Micro bên dưới để nói.</p>
                </div>`;
            document.getElementById('active-route-overlay').classList.remove('active');
            if (routePolyline) { map.removeLayer(routePolyline); routePolyline = null; }
            mapMarkers.forEach(m => map.removeLayer(m)); mapMarkers = [];
        }

        async function sendMessage() {
            const inputEl = document.getElementById('user-input');
            const query = inputEl.value.trim();
            if (!query) return;

            inputEl.value = '';
            const emptyState = document.getElementById('empty-state');
            if (emptyState) emptyState.style.display = 'none';

            const chatHistory = document.getElementById('chat-history');
            
            // User message
            const userRow = document.createElement('div');
            userRow.className = 'msg-row user';
            userRow.innerHTML = `<span class="msg-name">Bạn</span><div class="msg-bubble">${query}</div>`;
            chatHistory.appendChild(userRow);

            // AI Skeleton
            const aiRow = document.createElement('div');
            aiRow.className = 'msg-row ai';
            aiRow.innerHTML = `<span class="msg-name">AI Assistant</span><div class="msg-bubble">Đang xử lý...</div>`;
            chatHistory.appendChild(aiRow);
            chatHistory.scrollTop = chatHistory.scrollHeight;

            try {
                const response = await fetch('http://localhost:8000/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: query, force_offline: false })
                });

                const data = await response.json();
                let html = `<p>${data.reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')}</p>`;

                if (data.recommendations && data.recommendations.length > 0) {
                    html += '<div class="routes-grid">';
                    data.recommendations.forEach(r => {
                        const color = routeColor(r.route_id);
                        html += `
                            <div class="route-card" style="border-left-color:${color};" onclick="drawRouteOnMap('${r.board_stop}', '${r.alight_stop}', '${r.itinerary || ''}')">
                                <div class="card-header">
                                    <span class="route-badge" style="background:${color};">${r.route_id.replace('->', '➔')}</span>
                                    <span class="fare-badge">${r.fare_vnd.toLocaleString('vi-VN')} VNĐ</span>
                                </div>
                                <div class="card-title">${r.route_name}</div>
                            </div>`;
                    });
                    html += '</div>';
                    drawRouteOnMap(data.recommendations[0].board_stop, data.recommendations[0].alight_stop, data.recommendations[0].itinerary || '');
                }

                html += `<div class="msg-meta"><span style="color:var(--success)">${data.mode}</span> • <span>${data.processing_time_ms}ms</span></div>`;
                aiRow.querySelector('.msg-bubble').innerHTML = html;
                chatHistory.scrollTop = chatHistory.scrollHeight;

                let ttsText = data.reply;
                if (data.recommendations && data.recommendations.length > 0) {
                    ttsText = `Chuyến xe buýt phù hợp nhất là: ${data.recommendations[0].route_name.replace('Google Maps: ', '')}`;
                }
                speakVietnamese(ttsText);

            } catch (err) {
                aiRow.querySelector('.msg-bubble').innerHTML = `<p style="color: var(--danger)">Lỗi kết nối tới máy chủ AI.</p>`;
            }
        }
    </script>
</body>
</html>
"""

with open(r"e:\project\AI_Smart_Bus_Stop_Assistant\kiosk_ui\index.html", "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)
