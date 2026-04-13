<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="mb-1">Student Dashboard</h2>
        <p class="text-muted mb-0">
          {{ profile.name || 'Student' }}
          <span v-if="profile.branch">| {{ profile.branch }}</span>
          <span v-if="profile.cgpa !== null && profile.cgpa !== undefined">| CGPA {{ profile.cgpa }}</span>
        </p>
      </div>
      <button @click="exportData" class="btn btn-outline-secondary">Export CSV</button>
    </div>

    <div v-if="message" class="alert alert-success">{{ message }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="input-group mb-3">
      <span class="input-group-text">Search</span>
      <input v-model="search" @input="loadDrives" class="form-control" placeholder="Search by company or title">
    </div>

    <h4>Available Placement Drives</h4>
    <div class="row">
      <div v-for="drive in drives" :key="drive.id" class="col-md-6 col-lg-4">
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="card-title">{{ drive.title }}</h5>
            <p class="mb-1"><strong>Company:</strong> {{ drive.company }}</p>
            <p class="mb-1"><strong>CGPA:</strong> {{ drive.min_cgpa }}</p>
            <p class="mb-1"><strong>Branch:</strong> {{ drive.branch || 'Any' }}</p>
            <p class="mb-3"><strong>Year:</strong> {{ drive.year || 'Any' }}</p>
            <button @click="apply(drive.id)" class="btn btn-success">Apply</button>
          </div>
        </div>
      </div>
    </div>

    <h4 class="mt-4">My Applications</h4>
    <div class="card">
      <div class="card-body">
        <div v-if="!applications.length" class="text-muted">No applications yet.</div>
        <table v-else class="table mb-0">
          <thead>
            <tr>
              <th>Drive</th>
              <th>Company</th>
              <th>Status</th>
              <th>Applied At</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in applications" :key="application.id">
              <td>{{ application.drive_title }}</td>
              <td>{{ application.company_name }}</td>
              <td>{{ application.status }}</td>
              <td>{{ formatDate(application.applied_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      profile: {},
      drives: [],
      applications: [],
      search: '',
      error: '',
      message: ''
    };
  },
  methods: {
    authHeaders() {
      return { Authorization: localStorage.getItem('token') };
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleString() : '-';
    },
    async loadProfile() {
      const response = await fetch('http://localhost:5000/api/student/profile', {
        headers: this.authHeaders()
      });
      this.profile = await response.json();
    },
    async loadDrives() {
      const query = this.search ? `?search=${encodeURIComponent(this.search)}` : '';
      const response = await fetch(`http://localhost:5000/api/drives${query}`, {
        headers: this.authHeaders()
      });
      this.drives = await response.json();
    },
    async loadApplications() {
      const response = await fetch('http://localhost:5000/api/student/applications', {
        headers: this.authHeaders()
      });
      this.applications = await response.json();
    },
    async apply(id) {
      this.error = '';
      this.message = '';
      const response = await fetch(`http://localhost:5000/api/apply/${id}`, {
        method: 'POST',
        headers: this.authHeaders()
      });
      const data = await response.json();
      if (response.ok) {
        this.message = data.message;
        this.loadApplications();
      } else {
        this.error = data.message || 'Could not apply';
      }
    },
    async exportData() {
      const response = await fetch('http://localhost:5000/api/student/export', {
        headers: this.authHeaders()
      });
      if (!response.ok) {
        this.error = 'Could not export application history';
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'placement-history.csv';
      link.click();
      window.URL.revokeObjectURL(url);
    }
  },
  mounted() {
    this.loadProfile();
    this.loadDrives();
    this.loadApplications();
  }
}
</script>
