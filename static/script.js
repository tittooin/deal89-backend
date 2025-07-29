// Deal Aggregator Frontend JavaScript

class DealAggregator {
    constructor() {
        this.deals = [];
        this.filteredDeals = [];
        this.currentFilter = 'all';
        this.isLoading = false;
        this.backendUrl = window.location.origin; // Use same origin since we're serving from FastAPI
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDeals();
    }

    setupEventListeners() {
        // Platform filter buttons
        document.querySelectorAll('.platform-filter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const platform = e.target.dataset.platform;
                this.filterDeals(platform);
                this.updateFilterButtons(e.target);
            });
        });

        // Refresh button
        document.getElementById('refreshDeals').addEventListener('click', () => {
            this.loadDeals(true);
        });

        // Scroll animation
        window.addEventListener('scroll', () => {
            this.animateCardsOnScroll();
        });
    }

    async loadDeals(forceRefresh = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        this.hideError();

        try {
            const url = `${this.backendUrl}/deals${forceRefresh ? '?refresh=true' : ''}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.deals = data.deals || [];
            this.filteredDeals = [...this.deals];
            
            this.renderDeals();
            this.updateDealCount();
            
        } catch (error) {
            console.error('Error loading deals:', error);
            this.showError('Failed to load deals. Please check your internet connection and try again.');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    filterDeals(platform) {
        this.currentFilter = platform;
        
        if (platform === 'all') {
            this.filteredDeals = [...this.deals];
        } else {
            this.filteredDeals = this.deals.filter(deal => deal.platform === platform);
        }
        
        this.renderDeals();
        this.updateDealCount();
    }

    updateFilterButtons(activeBtn) {
        document.querySelectorAll('.platform-filter').forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }

    renderDeals() {
        const container = document.getElementById('dealsContainer');
        
        if (this.filteredDeals.length === 0) {
            container.innerHTML = this.getEmptyStateHTML();
            return;
        }

        const dealsHTML = this.filteredDeals.map((deal, index) => {
            return this.createDealCardHTML(deal, index);
        }).join('');

        container.innerHTML = dealsHTML;
        
        // Animate cards
        setTimeout(() => {
            document.querySelectorAll('.deal-card').forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('visible');
                }, index * 100);
            });
        }, 100);
    }

    createDealCardHTML(deal, index) {
        const platformClass = `platform-${deal.platform}`;
        const discountText = deal.discount_percentage > 0 ? 
            `<span class="discount-badge">${deal.discount_percentage}% OFF</span>` : '';
        
        const originalPriceHTML = deal.original_price && deal.original_price !== deal.current_price ?
            `<span class="original-price">${deal.original_price}</span>` : '';

        return `
            <div class="col-lg-4 col-md-6 col-sm-12 mb-4">
                <div class="card deal-card" data-deal-id="${deal.id}" data-platform="${deal.platform}">
                    <div class="card-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="platform-badge ${platformClass}">
                                ${this.getPlatformIcon(deal.platform)} ${deal.platform.toUpperCase()}
                            </span>
                            ${discountText}
                        </div>
                    </div>
                    <div class="card-body">
                        <h5 class="deal-title">${this.escapeHtml(deal.title)}</h5>
                        <div class="price-section">
                            <span class="current-price">${deal.current_price}</span>
                            ${originalPriceHTML}
                        </div>
                        <div class="deal-meta text-muted small">
                            <i class="fas fa-clock"></i> Updated recently
                        </div>
                    </div>
                    <div class="card-footer">
                        <button class="btn unlock-btn" 
                                onclick="dealAggregator.unlockDeal('${deal.id}', '${deal.platform}', this)">
                            <span class="btn-text">
                                <i class="fas fa-unlock"></i>
                                Unlock Deal for ₹0.89
                            </span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getPlatformIcon(platform) {
        const icons = {
            'flipkart': '<i class="fas fa-shopping-cart"></i>',
            'amazon': '<i class="fab fa-amazon"></i>',
            'jiomart': '<i class="fas fa-store"></i>',
            'myntra': '<i class="fas fa-tshirt"></i>',
            'swiggy': '<i class="fas fa-utensils"></i>',
            'bigbasket': '<i class="fas fa-shopping-basket"></i>'
        };
        return icons[platform] || '<i class="fas fa-shopping-bag"></i>';
    }

    async unlockDeal(dealId, platform, button) {
        if (button.classList.contains('btn-loading')) return;
        
        try {
            // Show loading state
            button.classList.add('btn-loading');
            button.innerHTML = `
                <span class="btn-text">
                    <div class="spinner-border spinner-border-sm" role="status"></div>
                    Processing...
                </span>
            `;

            // Create Razorpay order
            const orderResponse = await fetch(`${this.backendUrl}/create_order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    deal_id: dealId,
                    platform: platform
                })
            });

            if (!orderResponse.ok) {
                throw new Error('Failed to create order');
            }

            const orderData = await orderResponse.json();
            
            // Initialize Razorpay checkout
            this.initializeRazorpayCheckout(orderData, dealId, platform, button);

        } catch (error) {
            console.error('Error creating order:', error);
            this.showError('Failed to process payment. Please try again.');
            this.resetButton(button);
        }
    }

    initializeRazorpayCheckout(orderData, dealId, platform, button) {
        const options = {
            key: orderData.key,
            amount: orderData.amount,
            currency: orderData.currency,
            order_id: orderData.order_id,
            name: 'DealAggregator',
            description: 'Unlock exclusive deal access',
            image: '/static/logo.png', // Add your logo
            handler: async (response) => {
                await this.verifyPayment(response, dealId, platform, button);
            },
            prefill: {
                name: 'Customer',
                email: 'customer@example.com',
                contact: '9999999999'
            },
            theme: {
                color: '#007bff'
            },
            modal: {
                ondismiss: () => {
                    this.resetButton(button);
                }
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();
    }

    async verifyPayment(paymentResponse, dealId, platform, button) {
        try {
            const verifyResponse = await fetch(`${this.backendUrl}/verify_payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    payment_id: paymentResponse.razorpay_payment_id,
                    order_id: paymentResponse.razorpay_order_id,
                    signature: paymentResponse.razorpay_signature,
                    deal_id: dealId,
                    platform: platform
                })
            });

            if (!verifyResponse.ok) {
                throw new Error('Payment verification failed');
            }

            const verifyData = await verifyResponse.json();
            
            if (verifyData.success) {
                this.handleSuccessfulPayment(verifyData.affiliate_link, verifyData.deal_title, button);
            } else {
                throw new Error('Payment verification failed');
            }

        } catch (error) {
            console.error('Error verifying payment:', error);
            this.showError('Payment verification failed. Please contact support if amount was deducted.');
            this.resetButton(button);
        }
    }

    handleSuccessfulPayment(affiliateLink, dealTitle, button) {
        // Update button to show success
        button.classList.remove('btn-loading');
        button.classList.add('btn-success');
        button.innerHTML = `
            <span class="btn-text">
                <i class="fas fa-check"></i>
                Deal Unlocked!
            </span>
        `;

        // Show success message
        this.showSuccessMessage(`Deal unlocked successfully! Opening ${dealTitle}...`);

        // Open affiliate link in new tab
        setTimeout(() => {
            window.open(affiliateLink, '_blank');
        }, 1000);

        // Reset button after delay
        setTimeout(() => {
            this.resetButton(button, true);
        }, 3000);
    }

    resetButton(button, showUnlocked = false) {
        button.classList.remove('btn-loading', 'btn-success');
        
        if (showUnlocked) {
            button.innerHTML = `
                <span class="btn-text">
                    <i class="fas fa-external-link-alt"></i>
                    View Deal
                </span>
            `;
        } else {
            button.innerHTML = `
                <span class="btn-text">
                    <i class="fas fa-unlock"></i>
                    Unlock Deal for ₹0.89
                </span>
            `;
        }
    }

    showLoading(show) {
        const container = document.getElementById('loadingContainer');
        container.style.display = show ? 'block' : 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        errorText.textContent = message;
        errorDiv.classList.remove('d-none');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    hideError() {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.classList.add('d-none');
    }

    showSuccessMessage(message) {
        // Create and show success message
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        
        document.querySelector('.container').insertBefore(successDiv, document.getElementById('dealsContainer'));
        
        // Remove after 3 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    updateDealCount() {
        const countElement = document.getElementById('dealCount');
        countElement.textContent = `${this.filteredDeals.length} deals found`;
    }

    getEmptyStateHTML() {
        return `
            <div class="col-12">
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No deals found</h3>
                    <p>Try refreshing or selecting a different platform.</p>
                    <button class="btn btn-primary" onclick="dealAggregator.loadDeals(true)">
                        <i class="fas fa-sync-alt"></i> Refresh Deals
                    </button>
                </div>
            </div>
        `;
    }

    animateCardsOnScroll() {
        const cards = document.querySelectorAll('.deal-card:not(.visible)');
        const windowHeight = window.innerHeight;
        
        cards.forEach(card => {
            const cardTop = card.getBoundingClientRect().top;
            if (cardTop < windowHeight - 100) {
                card.classList.add('visible');
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dealAggregator = new DealAggregator();
});

// Handle page visibility change to refresh deals
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.dealAggregator) {
        // Refresh deals when user returns to tab
        setTimeout(() => {
            window.dealAggregator.loadDeals();
        }, 1000);
    }
});
