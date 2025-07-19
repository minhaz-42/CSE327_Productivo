// Helper functions for the Task Planner app

/**
 * Format date to readable string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date (e.g., "Dec 15, 2023 at 3:00 PM")
 */
function formatDate(dateString) {
  const options = { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit', 
    minute: '2-digit',
    hour12: true
  };
  return new Date(dateString).toLocaleString('en-US', options);
}

/**
 * Get priority color class
 * @param {string} priority - Priority level ('low', 'medium', 'high')
 * @returns {string} CSS class for the priority
 */
function getPriorityClass(priority) {
  const priorityClasses = {
    low: 'priority-badge low',
    medium: 'priority-badge medium',
    high: 'priority-badge high'
  };
  return priorityClasses[priority] || '';
}

/**
 * Check if a task is overdue
 * @param {string} deadline - Task deadline in ISO format
 * @returns {boolean} True if task is overdue
 */
function isOverdue(deadline) {
  return new Date(deadline) < new Date();
}

/**
 * Debounce function to limit how often a function is called
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Capitalize the first letter of a string
 * @param {string} str - Input string
 * @returns {string} Capitalized string
 */
function capitalizeFirstLetter(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Generate a unique ID
 * @returns {string} Unique ID
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Validate task form inputs
 * @param {Object} formData - Form data object
 * @returns {Object} { isValid: boolean, errors: Array<string> }
 */
function validateTaskForm(formData) {
  const errors = [];
  
  if (!formData.title || formData.title.trim().length < 3) {
    errors.push('Title must be at least 3 characters long');
  }
  
  if (!formData.deadline) {
    errors.push('Deadline is required');
  } else if (new Date(formData.deadline) < new Date()) {
    errors.push('Deadline must be in the future');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// Export functions for use in other files
export {
  formatDate,
  getPriorityClass,
  isOverdue,
  debounce,
  capitalizeFirstLetter,
  generateId,
  validateTaskForm
};