// DOM Elements
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const themeToggle = document.getElementById('themeToggle');
const notificationBtn = document.getElementById('notificationBtn');
const notificationPanel = document.getElementById('notificationPanel');
const taskForm = document.getElementById('taskForm');
const todayTasks = document.getElementById('todayTasks');
const upcomingTasks = document.getElementById('upcomingTasks');

// Sample Tasks Data
let tasks = [
  {
    id: 1,
    title: 'Complete project proposal',
    description: 'Finish the proposal document and send to client',
    priority: 'high',
    deadline: '2023-12-15T15:00',
    completed: false
  },
  {
    id: 2,
    title: 'Team meeting',
    description: 'Weekly team sync at 10am',
    priority: 'medium',
    deadline: '2023-12-14T10:00',
    completed: true
  },
  {
    id: 3,
    title: 'Client presentation',
    description: 'Prepare slides for quarterly review',
    priority: 'high',
    deadline: '2023-12-18T14:00',
    completed: false
  },
  {
    id: 4,
    title: 'Update documentation',
    description: 'Update API documentation for new features',
    priority: 'low',
    deadline: '2023-12-20T16:00',
    completed: false
  }
];

// Initialize the app
function init() {
  // Load tasks
  renderTasks();
  
  // Set up event listeners
  setupEventListeners();
  
  // Load theme preference
  loadThemePreference();
}

// Set up event listeners
function setupEventListeners() {
  // Sidebar toggle
  sidebarToggle.addEventListener('click', toggleSidebar);
  
  // Theme toggle
  themeToggle.addEventListener('click', toggleTheme);
  
  // Notification button
  notificationBtn.addEventListener('click', toggleNotifications);
  
  // Task form submission
  taskForm.addEventListener('submit', handleTaskSubmit);
  
  // Close notifications when clicking outside
  document.addEventListener('click', (e) => {
    if (!notificationBtn.contains(e.target) && !notificationPanel.contains(e.target)) {
      notificationPanel.classList.add('hidden');
    }
  });
}

// Toggle sidebar visibility
function toggleSidebar() {
  sidebar.classList.toggle('open');
}

// Toggle between light and dark theme
function toggleTheme() {
  document.body.classList.toggle('dark-theme');
  const isDark = document.body.classList.contains('dark-theme');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  themeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}

// Load theme preference from localStorage
function loadThemePreference() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
  }
}

// Toggle notifications panel
function toggleNotifications() {
  notificationPanel.classList.toggle('hidden');
}

// Handle task form submission
function handleTaskSubmit(e) {
  e.preventDefault();
  
  const newTask = {
    id: Date.now(),
    title: document.getElementById('title').value,
    description: document.getElementById('description').value,
    priority: document.getElementById('priority').value,
    deadline: document.getElementById('deadline').value,
    completed: false
  };
  
  tasks.push(newTask);
  renderTasks();
  taskForm.reset();
  
  // Show success message
  showNotification('Task added successfully!', 'success');
}

// Render tasks to the DOM
function renderTasks() {
  // Clear existing tasks
  todayTasks.innerHTML = '';
  upcomingTasks.innerHTML = '';
  
  const today = new Date().toISOString().split('T')[0];
  
  tasks.forEach(task => {
    const taskElement = createTaskElement(task);
    
    // Check if task is due today
    const taskDate = task.deadline.split('T')[0];
    if (taskDate === today && !task.completed) {
      todayTasks.appendChild(taskElement);
    } else if (!task.completed) {
      upcomingTasks.appendChild(taskElement);
    }
  });
  
  // Add empty message if no tasks
  if (todayTasks.children.length === 0) {
    todayTasks.innerHTML = '<div class="empty-message">No tasks for today</div>';
  }
  
  if (upcomingTasks.children.length === 0) {
    upcomingTasks.innerHTML = '<div class="empty-message">No upcoming tasks</div>';
  }
}

// Create task HTML element
function createTaskElement(task) {
  const taskElement = document.createElement('div');
  taskElement.className = `task-item ${task.completed ? 'completed' : ''}`;
  
  taskElement.innerHTML = `
    <div class="task-header">
      <h4>${task.title}</h4>
      <span class="priority-badge ${task.priority}">${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}</span>
    </div>
    <p>${task.description}</p>
    <div class="task-actions">
      <button class="action-btn ${task.completed ? 'completed' : ''}" data-id="${task.id}">
        ${task.completed ? 'Completed' : 'Complete'}
      </button>
      <button class="action-btn delete" data-id="${task.id}">Delete</button>
    </div>
  `;
  
  // Add event listeners to action buttons
  const completeBtn = taskElement.querySelector('.action-btn:not(.delete)');
  const deleteBtn = taskElement.querySelector('.action-btn.delete');
  
  completeBtn.addEventListener('click', () => toggleTaskComplete(task.id));
  deleteBtn.addEventListener('click', () => deleteTask(task.id));
  
  return taskElement;
}

// Toggle task complete status
function toggleTaskComplete(taskId) {
  const taskIndex = tasks.findIndex(task => task.id === taskId);
  if (taskIndex !== -1) {
    tasks[taskIndex].completed = !tasks[taskIndex].completed;
    renderTasks();
  }
}

// Delete a task
function deleteTask(taskId) {
  tasks = tasks.filter(task => task.id !== taskId);
  renderTasks();
  showNotification('Task deleted successfully!', 'success');
}

// Show notification
function showNotification(message, type) {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notificationPanel.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);