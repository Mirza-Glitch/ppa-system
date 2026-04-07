<template>
  <div id="app">
    <nav class="navbar navbar-dark bg-dark px-3">
      <span class="navbar-brand">PPA System</span>
      <button v-if="isLoggedIn" @click="logout" class="btn btn-outline-light btn-sm">Logout</button>
    </nav>

    <div v-if="!isLoggedIn">
      <login-component @login-success="checkLogin"></login-component>
    </div>
    
    <div v-else>
      <admin-dashboard v-if="role === 'admin'"></admin-dashboard>
      <company-dashboard v-if="role === 'company'"></company-dashboard>
      <student-dashboard v-if="role === 'student'"></student-dashboard>
    </div>
  </div>
</template>

<script>
import LoginComponent from './components/Login.vue';
import AdminDashboard from './components/AdminDashboard.vue';
import CompanyDashboard from './components/CompanyDashboard.vue';
import StudentDashboard from './components/StudentDashboard.vue';

export default {
  components: { LoginComponent, AdminDashboard, CompanyDashboard, StudentDashboard },
  data() {
    return { isLoggedIn: false, role: '' };
  },
  methods: {
    checkLogin() {
      const token = localStorage.getItem('token');
      if (token) {
        this.isLoggedIn = true;
        this.role = localStorage.getItem('role');
      }
    },
    logout() {
      localStorage.clear();
      this.isLoggedIn = false;
      this.role = '';
    }
  },
  mounted() { this.checkLogin(); }
}
</script>