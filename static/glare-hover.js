/**
 * Glare Hover Effect - Vanilla JavaScript
 * Applies a glare hover effect to all cards
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        cardSelector: '.card, .feature-card, .about-card, .team-card, .cta-card',
        glareClass: 'glare-hover',
        variants: ['glare-hover-purple', 'glare-hover-blue', 'glare-hover-pink']
    };

    /**
     * Apply glare effect to all cards
     */
    function applyGlareEffect() {
        const cards = document.querySelectorAll(config.cardSelector);
        
        console.log(`🔍 Found ${cards.length} cards to apply glare effect`);
        
        let appliedCount = 0;
        cards.forEach((card, index) => {
            // Skip if already has glare effect
            if (card.classList.contains(config.glareClass)) {
                console.log(`⏭️  Card ${index} already has glare effect, skipping`);
                return;
            }

            // Add base glare class
            card.classList.add(config.glareClass);

            // Add variant class (cycle through variants)
            const variantIndex = index % config.variants.length;
            card.classList.add(config.variants[variantIndex]);
            
            appliedCount++;
            console.log(`✨ Applied ${config.variants[variantIndex]} to card ${index}`);
        });

        console.log(`✅ Glare effect applied to ${appliedCount} cards (${cards.length} total found)`);
    }

    /**
     * Apply glare effect to dynamically added cards
     */
    function observeDynamicCards() {
        // Create a MutationObserver to watch for new cards
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    // Check if the added node is a card or contains cards
                    if (node.nodeType === 1) { // Element node
                        if (node.matches && node.matches(config.cardSelector)) {
                            applyGlareToCard(node);
                        } else if (node.querySelectorAll) {
                            const newCards = node.querySelectorAll(config.cardSelector);
                            newCards.forEach(applyGlareToCard);
                        }
                    }
                });
            });
        });

        // Start observing the document body for changes
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Apply glare effect to a single card
     */
    function applyGlareToCard(card) {
        if (!card.classList.contains(config.glareClass)) {
            card.classList.add(config.glareClass);
            
            // Add a random variant
            const randomVariant = config.variants[Math.floor(Math.random() * config.variants.length)];
            card.classList.add(randomVariant);
        }
    }

    /**
     * Initialize glare effect
     */
    function init() {
        console.log('🚀 Glare Hover Effect script loaded');
        console.log('📋 Watching for:', config.cardSelector);
        
        // Apply to existing cards
        if (document.readyState === 'loading') {
            console.log('⏳ Waiting for DOM to load...');
            document.addEventListener('DOMContentLoaded', () => {
                console.log('✅ DOM loaded, applying glare effect');
                applyGlareEffect();
            });
        } else {
            console.log('✅ DOM already loaded, applying glare effect immediately');
            applyGlareEffect();
        }

        // Watch for dynamically added cards (like playlist items)
        observeDynamicCards();
        console.log('👀 Watching for dynamically added cards');
    }

    // Initialize
    init();

    // Expose function to manually apply glare effect
    window.applyGlareEffect = applyGlareEffect;
    console.log('🔧 window.applyGlareEffect() is available for manual use');

})();
