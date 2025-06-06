class NavigationTracker {
    constructor() {
        this.userId = null;
        this.sessionId = null;
        this.currentPage = null;
        this.pageStartTime = null;
        this.isGamePage = false;
        this.scrollDepth = 0;
        this.maxScrollDepth = 0;
        
        this.init();
    }
    
    init() {
        // Check if this is a game page first
        this.getCurrentPageName(); // This sets this.isGamePage
        
        // Only initialize if not a game page
        if (!this.isGamePage) {
            // Initialize user session
            this.initializeSession();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Log initial page visit
            this.logPageVisit();
        }
        
        // Set up beforeunload to end session
        window.addEventListener('beforeunload', () => {
            this.endSession();
        });
        
        // Set up visibility change to handle tab switching
        document.addEventListener('visibilitychange', () => {
            if (this.isGamePage) {
                return; // Don't handle visibility changes on game pages
            }
            
            if (document.hidden) {
                this.endSession();
            } else {
                this.initializeSession();
                this.logPageVisit();
            }
        });
    }
    
    async initializeSession() {
        try {
            const response = await fetch('/api/init_navigation_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    page: this.getCurrentPageName(),
                    url: window.location.pathname,
                    referrer: document.referrer
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.userId = data.user_id;
                this.sessionId = data.session_id;
            }
        } catch (error) {
            console.error('Error initializing navigation session:', error);
        }
    }
    
    setupEventListeners() {
        // Track clicks on all elements
        document.addEventListener('click', (event) => {
            this.handleClick(event);
        });
        
        // Track scroll events
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.handleScroll();
            }, 100);
        });
        
        // Track link clicks specifically
        document.addEventListener('click', (event) => {
            if (event.target.tagName === 'A' || event.target.closest('a')) {
                this.handleLinkClick(event);
            }
        });
    }
    
    getCurrentPageName() {
        const path = window.location.pathname;
        
        // Check if it's a game page (exclude from navigation tracking)
        if (path.includes('/round/') || path.includes('/start') || path.includes('/final')) {
            this.isGamePage = true;
            return null; // Don't track game pages
        }
        
        this.isGamePage = false;
        
        // Map paths to page names
        const pageMap = {
            '/': 'index',
            '/introduction': 'introduction',
            '/play': 'play',
            '/statistics': 'statistics',
            '/human-statistics': 'human-statistics',
            '/llm-leaderboard': 'llm-leaderboard',
            '/research-notes': 'research-notes',
            '/about': 'about'
        };
        
        return pageMap[path] || 'unknown';
    }
    
    async logPageVisit() {
        if (this.isGamePage || !this.userId) {
            return; // Don't log game pages or if user not initialized
        }
        
        const pageName = this.getCurrentPageName();
        if (!pageName) return;
        
        this.currentPage = pageName;
        this.pageStartTime = Date.now();
        this.maxScrollDepth = 0;
        
        try {
            await fetch('/api/log_page_visit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    page: pageName,
                    url: window.location.pathname,
                    entry_method: this.getEntryMethod()
                })
            });
        } catch (error) {
            console.error('Error logging page visit:', error);
        }
    }
    
    getEntryMethod() {
        const referrer = document.referrer;
        const currentDomain = window.location.hostname;
        
        if (!referrer) {
            return 'direct';
        }
        
        if (referrer.includes(currentDomain)) {
            return 'link';
        }
        
        return 'external';
    }
    
    async handleClick(event) {
        if (this.isGamePage || !this.userId) {
            return;
        }
        
        const element = event.target;
        const rect = element.getBoundingClientRect();
        
        const interactionData = {
            user_id: this.userId,
            type: 'click',
            element_type: element.tagName.toLowerCase(),
            element_id: element.id || null,
            element_class: element.className || null,
            coordinates: {
                x: event.clientX,
                y: event.clientY,
                element_x: rect.left,
                element_y: rect.top
            },
            scroll_position: window.pageYOffset
        };
        
        try {
            await fetch('/api/log_interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(interactionData)
            });
        } catch (error) {
            console.error('Error logging click:', error);
        }
    }
    
    async handleLinkClick(event) {
        if (this.isGamePage || !this.userId) {
            return;
        }
        
        const link = event.target.tagName === 'A' ? event.target : event.target.closest('a');
        if (!link) return;
        
        const href = link.href;
        const isExternal = !href.includes(window.location.hostname);
        
        const linkData = {
            user_id: this.userId,
            type: 'link_click',
            element_type: 'a',
            element_id: link.id || null,
            element_class: link.className || null,
            link_text: link.textContent.trim(),
            link_href: href,
            link_target: link.target || '_self',
            is_external: isExternal,
            coordinates: {
                x: event.clientX,
                y: event.clientY
            }
        };
        
        try {
            await fetch('/api/log_interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(linkData)
            });
        } catch (error) {
            console.error('Error logging link click:', error);
        }
    }
    
    async handleScroll() {
        if (this.isGamePage || !this.userId) {
            return;
        }
        
        const scrollTop = window.pageYOffset;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollDepth = documentHeight > 0 ? scrollTop / documentHeight : 0;
        
        this.maxScrollDepth = Math.max(this.maxScrollDepth, scrollDepth);
        
        const scrollData = {
            user_id: this.userId,
            type: 'scroll',
            scroll_position: scrollTop,
            scroll_depth: scrollDepth,
            max_scroll_depth: this.maxScrollDepth
        };
        
        try {
            await fetch('/api/log_interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(scrollData)
            });
        } catch (error) {
            console.error('Error logging scroll:', error);
        }
    }
    
    async endSession() {
        if (!this.userId || this.isGamePage) {
            return;
        }
        
        try {
            await fetch('/api/end_navigation_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId
                })
            });
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }
}

// Initialize navigation tracker when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.navigationTracker = new NavigationTracker();
});

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.navigationTracker = new NavigationTracker();
    });
} else {
    window.navigationTracker = new NavigationTracker();
}
