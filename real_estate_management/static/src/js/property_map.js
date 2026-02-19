// NO /** @odoo-module **/ directive — plain IIFE, no OWL

(function () {
    'use strict';

    // =====================================================
    // GLOBAL BOOT GUARD
    // =====================================================
    // Odoo's asset pipeline can load web.assets_frontend
    // bundles more than once in certain scenarios (debug
    // mode, SPA navigation, hot-reload in dev).
    // A window-level flag survives across ALL executions
    // of this script, so the second run exits immediately.
    if (window.__realEstateBooted) {
        console.warn('[RealEstate] Duplicate script execution detected — aborting.');
        return;
    }
    window.__realEstateBooted = true;

    // =====================================================
    // AI INVESTMENT NEWS TICKER
    // =====================================================

    function getCity() {
        try { return new URLSearchParams(window.location.search).get('city') || ''; }
        catch (e) { return ''; }
    }

    function insertTicker(newsText, city) {
        if (!newsText) return;

        var old = document.getElementById('ai-news-ticker-box');
        if (old) old.parentNode.removeChild(old);

        var isCity = !!(city);
        var badge  = isCity
            ? '<span style="background:#ef4444;color:#fff;padding:6px 18px;border-radius:50px;font-weight:800;font-size:12px;letter-spacing:1px;white-space:nowrap;flex-shrink:0;box-shadow:0 0 16px rgba(239,68,68,0.5);">&#x1F534; LIVE</span>'
            : '<span style="background:#f97316;color:#fff;padding:6px 18px;border-radius:50px;font-weight:800;font-size:12px;letter-spacing:1px;white-space:nowrap;flex-shrink:0;box-shadow:0 0 16px rgba(249,115,22,0.5);">&#x1F525; TRENDING</span>';

        var title = isCity
            ? '&#x1F4C8; Top Investment Opportunities in <b style="color:#fbbf24;font-size:17px;">' + city + '</b>'
            : '&#x1F3D9;&#xFE0F; Top Trending Properties';

        var safe = newsText
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        var wrapper = document.createElement('div');
        wrapper.id  = 'ai-news-ticker-box';
        wrapper.innerHTML =
            '<style>@keyframes _ai_scroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}</style>' +
            '<div style="background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 55%,#0891b2 100%);' +
                'border-radius:16px;padding:18px 24px;margin:12px 30px 20px;' +
                'box-shadow:0 8px 28px rgba(30,58,138,0.35);' +
                'border:1px solid rgba(255,255,255,0.25);">' +
                '<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap;">' +
                    badge +
                    '<div style="color:#fff;font-size:16px;font-weight:700;">' + title + '</div>' +
                '</div>' +
                '<div style="overflow:hidden;background:rgba(0,0,0,0.22);border-radius:10px;border-left:5px solid #fbbf24;">' +
                    '<div style="display:inline-flex;align-items:center;white-space:nowrap;' +
                               'animation:_ai_scroll 50s linear infinite;padding:10px 0;">' +
                        '<span style="padding:0 48px;color:#fff;font-size:15px;font-weight:500;line-height:1.6;">' + safe + '</span>' +
                        '<span style="color:#fbbf24;font-size:22px;padding:0 16px;">&#x25CF;</span>' +
                        '<span style="padding:0 48px;color:#fff;font-size:15px;font-weight:500;line-height:1.6;">' + safe + '</span>' +
                        '<span style="color:#fbbf24;font-size:22px;padding:0 16px;">&#x25CF;</span>' +
                    '</div>' +
                '</div>' +
            '</div>';

        var anchor  = document.getElementById('ai-ticker-anchor');
        var topBar  = document.getElementById('top-bar');
        var mapDisp = document.getElementById('map-display');
        var wrap    = document.getElementById('wrap');

        if (anchor)                              { anchor.appendChild(wrapper); }
        else if (topBar && topBar.parentNode)    { topBar.parentNode.insertBefore(wrapper, topBar.nextSibling); }
        else if (mapDisp && mapDisp.parentNode)  { mapDisp.parentNode.insertBefore(wrapper, mapDisp); }
        else if (wrap)                           { wrap.insertBefore(wrapper, wrap.firstChild); }
        else                                     { document.body.insertBefore(wrapper, document.body.firstChild); }
    }

    function loadTicker() {
        var city = getCity();
        console.log('[Ticker] Requesting news, city="' + city + '"');
        fetch('/api/investment-news?city=' + encodeURIComponent(city))
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data && data.news) insertTicker(data.news, data.city || '');
            })
            .catch(function (err) { console.error('[Ticker] Failed:', err); });
    }

    // =====================================================
    // PROPERTY MAP
    // =====================================================

    function initPropertyMap() {
        var dataEl   = document.getElementById('property-data');
        var legendEl = document.getElementById('category-legend');
        var mapEl    = document.getElementById('propertyMap');

        // Not the property map page — exit silently
        if (!dataEl || !legendEl || !mapEl) return;

        // If a previous (broken/partial) Leaflet init left a _leaflet_id,
        // clean it up completely before we start.
        if (mapEl._leaflet_id) {
            console.warn('[PropertyMap] Stale Leaflet state found — cleaning up before init');
            try {
                // L.Map keeps a registry keyed by _leaflet_id
                var staleMap = mapEl._leaflet_id && L && L.Map && L.Map._instances
                    ? L.Map._instances[mapEl._leaflet_id]
                    : null;
                if (staleMap) staleMap.remove();
            } catch (e) { /* ignore */ }
            mapEl._leaflet_id = null;
            mapEl.innerHTML   = '';
        }

        var properties = [];
        try {
            properties = JSON.parse(dataEl.dataset.properties || '[]');
            if (!Array.isArray(properties)) properties = [];
        } catch (e) { console.error('[PropertyMap] bad JSON', e); }

        var categoryColors = {};
        try {
            categoryColors = JSON.parse(legendEl.dataset.colors || '{}');
        } catch (e) { console.error('[PropertyMap] bad colors JSON', e); }

        console.log('[PropertyMap] ' + properties.length + ' properties');

        function waitForLeaflet(cb) {
            if (typeof L !== 'undefined') { cb(); return; }
            setTimeout(function () { waitForLeaflet(cb); }, 200);
        }

        waitForLeaflet(function () {
            console.log('[PropertyMap] Leaflet ready — initialising map');

            var map = L.map(mapEl);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(map);

            var openPopupMarker    = null;
            var pointerInsidePopup = false;

            function createIcon(color) {
                return L.divIcon({
                    className: 'custom-marker',
                    html: '<div style="width:32px;height:32px;border-radius:50%;' +
                          'background:' + color + ';border:3px solid white;' +
                          'box-shadow:0 3px 12px rgba(0,0,0,0.3);' +
                          'display:flex;align-items:center;justify-content:center;' +
                          'font-size:14px;color:white;cursor:pointer;">📍</div>',
                    iconSize: [32, 32], iconAnchor: [16, 16], popupAnchor: [0, -16]
                });
            }

            function popupHtml(p) {
                var img   = p.image_url || '/web/static/img/placeholder.png';
                var price = p.price > 0
                    ? '₹' + Number(p.price).toLocaleString('en-IN')
                    : 'Price on Request';
                return '<div class="property-hover-card">' +
                    '<img src="' + img + '" class="property-image" ' +
                         'onerror="this.src=\'/web/static/img/placeholder.png\'"/>' +
                    '<div class="property-content">' +
                        '<h4 class="property-title">' + (p.name || '') + '</h4>' +
                        '<div class="property-category">' + (p.property_type || '') + '</div>' +
                        '<div class="property-location">📍 ' + (p.full_address || '') + '</div>' +
                        '<div class="property-price">' + price + '</div>' +
                        '<div class="property-details">' +
                            (p.plot_area ? '<div class="detail-item">📐 ' + p.plot_area + ' sqft</div>' : '') +
                        '</div>' +
                        '<div class="action-buttons">' +
                            '<a href="/property/' + p.id + '" class="btn-sm btn-primary">View Details</a>' +
                            (p.contact_phone
                                ? '<a href="tel:' + p.contact_phone + '" class="btn-sm btn-outline">📞 Call</a>'
                                : '') +
                        '</div>' +
                    '</div></div>';
            }

            var markerLatLngs = [];

            properties.forEach(function (p) {
                if (!p.latitude || !p.longitude) return;

                var color  = categoryColors[p.property_type] || '#4f46e5';
                var marker = L.marker([p.latitude, p.longitude], {
                    icon: createIcon(color)
                }).addTo(map);
                markerLatLngs.push([p.latitude, p.longitude]);

                marker.bindPopup(popupHtml(p), {
                    closeButton: false, autoClose: false, closeOnClick: false,
                    className: 'custom-popup', minWidth: 280, maxWidth: 320
                });

                marker.on('mouseover', function () {
                    if (openPopupMarker && openPopupMarker !== marker) openPopupMarker.closePopup();
                    marker.openPopup();
                    openPopupMarker = marker;
                });

                marker.on('mouseout', function () {
                    setTimeout(function () {
                        if (openPopupMarker === marker && !pointerInsidePopup) {
                            marker.closePopup();
                            openPopupMarker = null;
                        }
                    }, 100);
                });

                marker.on('popupopen', function (ev) {
                    var popupEl = ev && ev.popup ? ev.popup.getElement() : null;
                    if (!popupEl) return;
                    popupEl.addEventListener('mouseenter', function () { pointerInsidePopup = true; });
                    popupEl.addEventListener('mouseleave', function () {
                        pointerInsidePopup = false;
                        setTimeout(function () {
                            if (openPopupMarker === marker && !pointerInsidePopup) {
                                marker.closePopup();
                                openPopupMarker = null;
                            }
                        }, 100);
                    });
                });
            });

            map.on('click', function () {
                if (openPopupMarker) { openPopupMarker.closePopup(); openPopupMarker = null; }
            });

            legendEl.innerHTML = Object.entries(categoryColors).map(function (e) {
                return '<div class="legend-item">' +
                       '<div class="legend-color" style="background:' + e[1] + '"></div>' +
                       '<span>' + e[0] + '</span></div>';
            }).join('');

            if (markerLatLngs.length === 1) {
                map.setView(markerLatLngs[0], 15);
            } else if (markerLatLngs.length > 1) {
                var grp    = L.featureGroup(markerLatLngs.map(function (ll) { return L.marker(ll); }));
                var bounds = grp.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds.pad(0.1));
                    if (map.getZoom() < 8) map.setView(bounds.getCenter(), 10);
                } else {
                    map.setView([20.5937, 78.9629], 5);
                }
            } else {
                map.setView([20.5937, 78.9629], 5);
            }

            setTimeout(function () { map.invalidateSize(); }, 300);
        });
    }

    // =====================================================
    // BOOT
    // =====================================================
    function boot() {
        loadTicker();
        initPropertyMap();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

})();