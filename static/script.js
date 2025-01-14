document.addEventListener("DOMContentLoaded", () => {
  // Hamburger menu and sidebar toggle elements
  const hamburgerMenu = document.getElementById("hamburger-menu");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.querySelector(".main-content");
  const toggleButton = document.getElementById("toggle-btn");

  // Event listener to toggle the sidebar visibility via hamburger menu click
  if (hamburgerMenu && sidebar && mainContent) {
      hamburgerMenu.addEventListener("click", () => {
          sidebar.classList.toggle("active"); // Show/hide sidebar
          mainContent.classList.toggle("shifted"); // Shift main content
      });
  }

  // Event listener to toggle sidebar visibility via toggle button inside sidebar
  if (toggleButton) {
      toggleButton.addEventListener("click", () => {
          sidebar.classList.toggle("active"); // Show/hide sidebar
          mainContent.classList.toggle("shifted"); // Shift main content
      });
  }

  // Hover effect to show sidebar when hovering over it
  sidebar.addEventListener("mouseover", () => {
      sidebar.classList.add("active"); // Open sidebar on hover
  });

  // Hide sidebar when mouse leaves it
  sidebar.addEventListener("mouseleave", () => {
      if (!sidebar.classList.contains("active")) {
          sidebar.classList.remove("active"); // Hide sidebar when not active
          mainContent.classList.remove("shifted"); // Remove shifted state from main content
      }
  });

  // Close sidebar when clicking outside of it
  document.addEventListener("click", (event) => {
      if (!sidebar.contains(event.target) && !hamburgerMenu.contains(event.target) && !toggleButton.contains(event.target)) {
          sidebar.classList.remove("active");
          mainContent.classList.remove("shifted");
      }
  });

  // Handle Login and Signup form navigation
  const loginTab = document.getElementById("login-tab");
  const signupTab = document.getElementById("signup-tab");
  const loginForm = document.getElementById("login-form");
  const signupForm = document.getElementById("signup-form");

  if (loginTab && signupTab && loginForm && signupForm) {
      loginTab.addEventListener("click", () => {
          loginForm.style.display = "block"; // Show Login Form
          signupForm.style.display = "none"; // Hide Signup Form
          loginTab.classList.add("active"); // Mark Login tab as active
          signupTab.classList.remove("active"); // Remove active class from Signup tab
      });

      signupTab.addEventListener("click", () => {
          loginForm.style.display = "none"; // Hide Login Form
          signupForm.style.display = "block"; // Show Signup Form
          signupTab.classList.add("active"); // Mark Signup tab as active
          loginTab.classList.remove("active"); // Remove active class from Login tab
      });
  }

  // Form validation for Signup
  const signupSubmit = document.getElementById("signup-submit");
  if (signupSubmit) {
      signupSubmit.addEventListener("click", (event) => {
          const password = document.getElementById("signup-password").value;
          const confirmPassword = document.getElementById("confirm-password").value;
          if (password !== confirmPassword) {
              event.preventDefault(); // Prevent form submission
              alert("Passwords do not match!");
          }
      });
  }
});
