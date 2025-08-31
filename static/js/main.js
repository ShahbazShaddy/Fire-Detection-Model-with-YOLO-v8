// Animation on scroll functionality
document.addEventListener("DOMContentLoaded", function() {
  // Add animation classes on scroll
  const animateElements = document.querySelectorAll('.process-step, .feature-card, .use-case-card, .testimonial-card, .stat-card, .demo-card');
  
  // FAQ accordion functionality
  const faqItems = document.querySelectorAll('.faq-item');
  
  // Intersection Observer for animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        if (entry.target.classList.contains('process-step')) {
          entry.target.classList.add('slide-up');
        } else if (entry.target.classList.contains('stat-card')) {
          entry.target.classList.add('scale-in');
        } else {
          entry.target.classList.add('fade-in');
        }
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.2
  });
  
  animateElements.forEach(element => {
    observer.observe(element);
  });
  
  // FAQ accordion
  faqItems.forEach(item => {
    const question = item.querySelector('h3');
    const answer = item.querySelector('p');
    
    // Initially hide answers
    answer.style.maxHeight = '0';
    answer.style.overflow = 'hidden';
    answer.style.transition = 'max-height 0.3s ease';
    answer.style.padding = '0';
    
    question.addEventListener('click', () => {
      const isOpen = answer.style.maxHeight !== '0px';
      
      // Close all other answers
      faqItems.forEach(otherItem => {
        if (otherItem !== item) {
          const otherAnswer = otherItem.querySelector('p');
          otherAnswer.style.maxHeight = '0';
          otherAnswer.style.padding = '0';
          otherItem.classList.remove('active');
        }
      });
      
      // Toggle current answer
      if (isOpen) {
        answer.style.maxHeight = '0';
        answer.style.padding = '0';
        item.classList.remove('active');
      } else {
        answer.style.maxHeight = answer.scrollHeight + 'px';
        answer.style.padding = '1rem 0 0';
        item.classList.add('active');
      }
    });
  });
  
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 80, // Offset for fixed header
          behavior: 'smooth'
        });
      }
    });
  });
  
  // Form validation and submission
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      // Basic validation
      const name = document.getElementById('name').value;
      const email = document.getElementById('email').value;
      const message = document.getElementById('message').value;
      
      if (!name || !email || !message) {
        alert('Please fill in all required fields');
        return;
      }
      
      // Show success message (in a real app, you would send the form data to a server)
      const formElements = contactForm.elements;
      for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = true;
      }
      
      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Sending...';
      
      // Simulate form submission
      setTimeout(() => {
        contactForm.innerHTML = `
          <div class="success-message">
            <i class="fas fa-check-circle" style="font-size: 3rem; color: var(--success-color); margin-bottom: 1rem;"></i>
            <h3>Message Sent Successfully!</h3>
            <p>Thank you for reaching out. We'll get back to you shortly.</p>
          </div>
        `;
      }, 1500);
    });
  }
  
  // Mobile navigation toggle
  const createMobileNav = () => {
    const nav = document.querySelector('nav');
    const navLinks = document.querySelector('.nav-links');
    
    if (nav && navLinks && !document.querySelector('.mobile-toggle')) {
      const mobileToggle = document.createElement('div');
      mobileToggle.className = 'mobile-toggle';
      mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
      
      nav.insertBefore(mobileToggle, navLinks);
      
      // Add styles for mobile navigation
      const style = document.createElement('style');
      style.textContent = `
        @media (max-width: 768px) {
          .nav-links {
            display: none;
            width: 100%;
            flex-direction: column;
            align-items: center;
            padding: 1rem 0;
          }
          
          .nav-links.active {
            display: flex;
          }
          
          .mobile-toggle {
            display: block;
            font-size: 1.5rem;
            color: white;
            cursor: pointer;
          }
        }
        
        @media (min-width: 769px) {
          .mobile-toggle {
            display: none;
          }
        }
      `;
      document.head.appendChild(style);
      
      mobileToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        const icon = mobileToggle.querySelector('i');
        if (navLinks.classList.contains('active')) {
          icon.className = 'fas fa-times';
        } else {
          icon.className = 'fas fa-bars';
        }
      });
    }
  };
  
  createMobileNav();
});

// Animated counter for stats
function animateCounters() {
  const statElements = document.querySelectorAll('.stat-card h3');
  
  statElements.forEach(statElement => {
    const targetValue = parseFloat(statElement.textContent);
    const suffix = statElement.textContent.replace(/[0-9.+]/g, '');
    let startValue = 0;
    const duration = 2000;
    const startTime = performance.now();
    
    function updateCount(currentTime) {
      const elapsedTime = currentTime - startTime;
      const progress = Math.min(elapsedTime / duration, 1);
      
      let currentValue;
      if (targetValue >= 100) {
        currentValue = Math.floor(progress * targetValue);
      } else {
        currentValue = (progress * targetValue).toFixed(1);
        if (currentValue.endsWith('.0')) {
          currentValue = parseInt(currentValue);
        }
      }
      
      statElement.textContent = currentValue + suffix;
      
      if (progress < 1) {
        requestAnimationFrame(updateCount);
      }
    }
    
    // Reset to zero before animation
    statElement.textContent = '0' + suffix;
    
    // Create observer to start animation when element is in view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          requestAnimationFrame(updateCount);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    
    observer.observe(statElement);
  });
}

// Call the animation function when stats section is in view
const statsSection = document.querySelector('.stats');
if (statsSection) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounters();
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });
  
  observer.observe(statsSection);
}