<template>
  <div class="container mt-5" style="max-width: 460px;">
    <div class="card p-4 shadow-sm">
      <h3 class="text-center mb-4">{{ isRegisterMode ? 'Create Account' : 'PPA Login' }}</h3>
      <div v-if="success" class="alert alert-success">{{ success }}</div>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>

      <form v-if="!isRegisterMode" @submit.prevent="handleLogin">
        <div class="mb-3">
          <label class="form-label">Email address</label>
          <input v-model="loginForm.email" type="email" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="loginForm.password" type="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">Login</button>
      </form>

      <form v-else @submit.prevent="handleRegister">
        <div class="mb-3">
          <label class="form-label">Full name</label>
          <input v-model="registerForm.name" type="text" class="form-control" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Role</label>
          <select v-model="registerForm.role" class="form-select" required>
            <option value="student">Student</option>
            <option value="company">Company</option>
          </select>
        </div>
        <div class="mb-3">
          <label class="form-label">Email address</label>
          <input v-model="registerForm.email" type="email" class="form-control" required>
        </div>
        <div class="mb-3" v-if="registerForm.role === 'student'">
          <label class="form-label">CGPA</label>
          <input
            v-model="registerForm.cgpa"
            type="number"
            min="0"
            max="10"
            step="0.01"
            class="form-control"
            required
          >
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="registerForm.password" type="password" class="form-control" minlength="8" required>
        </div>
        <button type="submit" class="btn btn-success w-100">Create Account</button>
      </form>

      <p class="mt-3 text-center mb-0">
        <template v-if="isRegisterMode">
          Already have an account?
          <a href="#" @click.prevent="switchMode(false)">Back to Login</a>
        </template>
        <template v-else>
          Need an account?
          <a href="#" @click.prevent="switchMode(true)">Register as Student or Company</a>
        </template>
      </p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isRegisterMode: false,
      error: '',
      success: '',
      loginForm: {
        email: '',
        password: ''
      },
      registerForm: {
        name: '',
        role: 'student',
        email: '',
        cgpa: '',
        password: ''
      }
    };
  },
  methods: {
    switchMode(isRegisterMode, preserveMessages = false) {
      this.isRegisterMode = isRegisterMode;
      if (!preserveMessages) {
        this.error = '';
        this.success = '';
      }
    },
    async handleLogin() {
      this.error = '';
      this.success = '';

      try {
        const response = await fetch('http://localhost:5000/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.loginForm)
        });
        const data = await response.json();
        if (response.ok) {
          localStorage.setItem('token', data.token);
          localStorage.setItem('role', data.role);
          this.$emit('login-success');
        } else {
          this.error = data.message || 'Invalid credentials';
        }
      } catch (err) {
        this.error = 'Server error. Please try again.';
      }
    },
    async handleRegister() {
      this.error = '';
      this.success = '';

      const payload = {
        ...this.registerForm,
        cgpa: this.registerForm.role === 'student' ? this.registerForm.cgpa : null
      };

      try {
        const response = await fetch('http://localhost:5000/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok) {
          this.registerForm = {
            name: '',
            role: 'student',
            email: '',
            cgpa: '',
            password: ''
          };
          this.success = `${data.message}. You can log in now.`;
          this.switchMode(false, true);
        } else {
          this.error = data.message || 'Registration failed';
        }
      } catch (err) {
        this.error = 'Server error. Please try again.';
      }
    }
  }
}
</script>
