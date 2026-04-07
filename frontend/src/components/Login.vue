<template>
  <div class="container mt-5" style="max-width: 400px;">
    <div class="card p-4 shadow-sm">
      <h3 class="text-center mb-4">PPA Login</h3>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label class="form-label">Email address</label>
          <input v-model="email" type="email" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>
      <p class="mt-3 text-center">
        Need an account? <a href="#">Register as Student or Company</a>
      </p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return { email: '', password: '', error: '' };
  },
  methods: {
    async handleLogin() {
      try {
        const response = await fetch('http://localhost:5000/login?include_auth_token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        });
        const data = await response.json();
        if (response.ok) {
          localStorage.setItem('token', data.response.user.authentication_token);
          localStorage.setItem('role', data.response.user.roles[0]);
          this.$emit('login-success'); // Notify App.vue to change view
        } else {
          this.error = "Invalid credentials";
        }
      } catch (err) {
        this.error = "Server error. Please try again.";
      }
    }
  }
}
</script>