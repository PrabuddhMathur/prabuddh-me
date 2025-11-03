/**
 * Mobile Header Hide-on-Scroll Feature
 * Hides the header when scrolling down and shows it when scrolling up
 * Only applies on mobile devices (below 1024px)
 */

(function() {
    let lastScrollTop = 0;
    let isScrolling = false;
    let scrollPositionWhenHidden = 0; // Track where we were when header was hidden
    const scrollThreshold = 50; // Minimum scroll distance to trigger hide
    const showThreshold = 120; // Minimum upward scroll distance to show header again
    const header = document.querySelector('nav');
    
    if (!header) return;
    
    function isMobileViewport() {
        return window.innerWidth < 1024; // lg breakpoint in Tailwind
    }
    
    function handleScroll() {
        // Only apply on mobile devices
        if (!isMobileViewport()) {
            header.classList.remove('header-hidden');
            return;
        }
        
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
        // Prevent negative scrolling issues on mobile
        if (currentScroll <= 0) {
            header.classList.remove('header-hidden');
            return;
        }
        
        // Check if we've scrolled past the threshold
        if (Math.abs(currentScroll - lastScrollTop) < scrollThreshold) {
            return;
        }
        
        // Scrolling down - hide header
        if (currentScroll > lastScrollTop && currentScroll > scrollThreshold) {
            if (!header.classList.contains('header-hidden')) {
                // Remember where we were when we hid the header
                scrollPositionWhenHidden = currentScroll;
            }
            header.classList.add('header-hidden');
        }
        // Scrolling up - show header only after meaningful upward scroll
        else if (currentScroll < lastScrollTop) {
            // Only show header if user has scrolled up significantly from where it was hidden
            const upwardScrollDistance = scrollPositionWhenHidden - currentScroll;
            if (upwardScrollDistance >= showThreshold) {
                header.classList.remove('header-hidden');
            }
        }
        
        lastScrollTop = currentScroll;
    }
    
    // Throttle scroll events for better performance
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
    
    // Handle window resize - reset state if switching to desktop
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (!isMobileViewport()) {
                header.classList.remove('header-hidden');
            }
        }, 250);
    }, { passive: true });
    
    // Check mobile menu state - don't hide header if menu is open
    const mobileMenuObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const mobileMenu = document.querySelector('#mobile-menu');
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    // Mobile menu is open, show header
                    header.classList.remove('header-hidden');
                }
            }
        });
    });
    
    // Observe mobile menu for changes
    const mobileMenu = document.querySelector('#mobile-menu');
    if (mobileMenu) {
        mobileMenuObserver.observe(mobileMenu, { attributes: true });
    }
})();