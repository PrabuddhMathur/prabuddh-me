/**
 * Spoiler Text Click-to-Reveal Functionality
 * 
 * Implements Reddit-style spoiler behavior:
 * - Blurred text reveals on click
 * - Revealed state persists until page refresh
 * - Keyboard accessible (Enter/Space)
 * - Uses event delegation for efficiency
 * 
 * Vanilla JavaScript - no dependencies required
 */

(function() {
    'use strict';

    /**
     * Initialize spoiler elements with accessibility attributes
     */
    function initializeSpoilers() {
        const spoilers = document.querySelectorAll('.spoiler[data-spoiler="true"]');
        
        spoilers.forEach(function(spoiler) {
            // Skip if already initialized
            if (spoiler.hasAttribute('data-spoiler-initialized')) {
                return;
            }
            
            // Add accessibility attributes
            spoiler.setAttribute('role', 'button');
            spoiler.setAttribute('tabindex', '0');
            spoiler.setAttribute('aria-label', 'Spoiler text - click to reveal');
            spoiler.setAttribute('aria-pressed', 'false');
            
            // Prevent text selection on rapid clicks
            spoiler.addEventListener('mousedown', function(e) {
                if (e.detail > 1) {
                    e.preventDefault();  // Prevents text selection on double/triple click
                }
            });
            
            // Mark as initialized
            spoiler.setAttribute('data-spoiler-initialized', 'true');
        });
    }

    /**
     * Toggle spoiler visibility
     * @param {HTMLElement} spoiler - The spoiler element to toggle
     */
    function toggleSpoiler(spoiler) {
        // Toggle revealed class
        spoiler.classList.toggle('revealed');
        
        // Check current state
        const isRevealed = spoiler.classList.contains('revealed');
        
        // Update accessibility attributes based on state
        if (isRevealed) {
            spoiler.setAttribute('aria-label', 'Spoiler text - revealed, click to hide');
            spoiler.setAttribute('aria-pressed', 'true');
        } else {
            spoiler.setAttribute('aria-label', 'Hidden spoiler text - click to reveal');
            spoiler.setAttribute('aria-pressed', 'false');
        }
        
        // Fire custom event (optional, for analytics or other integrations)
        const event = new CustomEvent('spoiler:toggled', {
            detail: {
                element: spoiler,
                revealed: isRevealed,
                text: spoiler.textContent
            },
            bubbles: true
        });
        spoiler.dispatchEvent(event);
    }

    /**
     * Handle click events on spoiler elements
     * @param {Event} e - The click event
     */
    function handleClick(e) {
        const spoiler = e.target.closest('.spoiler[data-spoiler="true"]');
        
        // Only handle spoiler clicks
        if (!spoiler) {
            return;
        }
        
        // Prevent default behavior
        e.preventDefault();
        
        // Toggle the spoiler
        toggleSpoiler(spoiler);
    }

    /**
     * Handle keyboard events on spoiler elements
     * @param {KeyboardEvent} e - The keyboard event
     */
    function handleKeyboard(e) {
        const spoiler = e.target.closest('.spoiler[data-spoiler="true"]');
        
        // Only handle spoiler key presses
        if (!spoiler) {
            return;
        }
        
        // Check for Enter or Space key
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleSpoiler(spoiler);
        }
    }

    /**
     * Initialize the spoiler functionality
     */
    function init() {
        // Initialize existing spoilers
        initializeSpoilers();
        
        // Set up event delegation for clicks
        document.addEventListener('click', handleClick);
        
        // Set up event delegation for keyboard
        document.addEventListener('keydown', handleKeyboard);
        
        // Re-initialize on dynamic content changes (for SPAs or AJAX)
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        initializeSpoilers();
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();