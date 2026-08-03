(function () {
    const overlayId = "globalLoadingOverlay";
    let activeRequests = 0;

    function ensureOverlay() {
        if (document.getElementById(overlayId)) {
            return document.getElementById(overlayId);
        }

        const overlay = document.createElement("div");
        overlay.id = overlayId;
        overlay.className = "global-loading-overlay";
        overlay.innerHTML = `
            <div class="global-loading-spinner" aria-label="Loading"></div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }

    function showLoader() {
        const overlay = ensureOverlay();
        activeRequests += 1;
        overlay.style.display = "flex";
    }

    function hideLoader() {
        activeRequests = Math.max(0, activeRequests - 1);
        if (activeRequests === 0) {
            const overlay = document.getElementById(overlayId);
            if (overlay) {
                overlay.style.display = "none";
            }
        }
    }

    function interceptFetch() {
        const originalFetch = window.fetch.bind(window);
        window.fetch = function (...args) {
            showLoader();
            return Promise.resolve(originalFetch(...args)).finally(hideLoader);
        };
    }

    function interceptXHR() {
        if (!window.XMLHttpRequest) return;
        const XHR = window.XMLHttpRequest;
        const origOpen = XHR.prototype.open;
        const origSend = XHR.prototype.send;

        XHR.prototype.open = function (...args) {
            this._lm_openArgs = args;
            return origOpen.apply(this, args);
        };

        XHR.prototype.send = function (...args) {
            // only intercept real requests
            try {
                showLoader();
                this.addEventListener('loadend', hideLoader);
                this.addEventListener('error', hideLoader);
                this.addEventListener('abort', hideLoader);
            } catch (e) {
                // ignore
            }
            return origSend.apply(this, args);
        };
    }

    // Show overlay immediately when navigating away (refresh/back) so user sees feedback
    window.addEventListener('beforeunload', () => {
        const overlay = ensureOverlay();
        overlay.style.display = 'flex';
    });

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            ensureOverlay();
            interceptFetch();
            interceptXHR();
        });
    } else {
        ensureOverlay();
        interceptFetch();
        interceptXHR();
    }
})();
