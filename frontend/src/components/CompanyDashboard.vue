<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h2 class="mb-1">Company Dashboard</h2>
        <p class="text-muted mb-0">
          {{ company.name || 'Company' }} |
          Status:
          <span :class="company.approved ? 'text-success' : 'text-warning'">
            {{ company.approved ? 'Approved' : 'Pending Approval' }}
          </span>
        </p>
      </div>
      <button class="btn btn-primary" @click="showForm = !showForm">
        {{ showForm ? 'Close Form' : 'Create Drive' }}
      </button>
    </div>

    <div v-if="message" class="alert alert-success">{{ message }}</div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="showForm" class="card p-3 mb-4 bg-light">
      <h5>New Placement Drive</h5>
      <input v-model="newDrive.title" class="form-control mb-2" placeholder="Job Title">
      <textarea v-model="newDrive.desc" class="form-control mb-2" placeholder="Description"></textarea>
      <div class="row">
        <div class="col-md-3">
          <input v-model="newDrive.cgpa" type="number" step="0.1" class="form-control mb-2" placeholder="Min CGPA">
        </div>
        <div class="col-md-3">
          <input v-model="newDrive.branch" class="form-control mb-2" placeholder="Branch">
        </div>
        <div class="col-md-3">
          <input v-model="newDrive.year" type="number" class="form-control mb-2" placeholder="Year">
        </div>
        <div class="col-md-3">
          <input v-model="newDrive.deadline" type="datetime-local" class="form-control mb-2">
        </div>
      </div>
      <input v-model="newDrive.location" class="form-control mb-2" placeholder="Location">
      <input v-model="newDrive.package_amount" class="form-control mb-2" placeholder="Package / CTC">
      <button @click="createDrive" class="btn btn-success" :disabled="!company.approved">
        Submit for Approval
      </button>
    </div>

    <h4>Your Drives</h4>
    <div v-if="!myDrives.length" class="card card-body text-muted">No drives created yet.</div>

    <div v-for="drive in myDrives" :key="drive.id" class="card mb-3">
      <div class="card-header d-flex justify-content-between align-items-center">
        <div>
          <strong>{{ drive.title }}</strong>
          <div class="small text-muted">{{ drive.location || 'Location not set' }}</div>
        </div>
        <span class="badge bg-secondary">{{ drive.status }}</span>
      </div>
      <div class="card-body">
        <p class="mb-2">{{ drive.description }}</p>
        <p class="small text-muted mb-3">
          Min CGPA: {{ drive.min_cgpa }} |
          Branch: {{ drive.branch || 'Any' }} |
          Year: {{ drive.year || 'Any' }}
        </p>

        <h6>Applicants</h6>
        <div v-if="!drive.applicants.length" class="text-muted">No applications yet.</div>
        <div v-for="app in drive.applicants" :key="app.id" class="border rounded p-2 mb-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>{{ app.student_name }}</strong>
              <div class="small text-muted">{{ app.student_email }}</div>
            </div>
            <span class="badge bg-info text-dark">{{ app.status }}</span>
          </div>
          <div class="mt-2">
            <button @click="updateStatus(app.id, 'Shortlisted')" class="btn btn-sm btn-outline-primary me-2">Shortlist</button>
            <button @click="updateStatus(app.id, 'Selected')" class="btn btn-sm btn-outline-success me-2">Select</button>
            <button @click="updateStatus(app.id, 'Rejected')" class="btn btn-sm btn-outline-danger">Reject</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      company: {},
      showForm: false,
      message: '',
      error: '',
      newDrive: {
        title: '',
        desc: '',
        cgpa: 0,
        branch: '',
        year: '',
        deadline: '',
        location: '',
        package_amount: ''
      },
      myDrives: []
    };
  },
  methods: {
    authHeaders(json = false) {
      return json
        ? { 'Content-Type': 'application/json', Authorization: localStorage.getItem('token') }
        : { Authorization: localStorage.getItem('token') };
    },
    async fetchDrives() {
      const res = await fetch('http://localhost:5000/api/company/drives', {
        headers: this.authHeaders()
      });
      const data = await res.json();
      this.company = data.company || {};
      this.myDrives = data.drives || [];
    },
    async createDrive() {
      this.message = '';
      this.error = '';
      const res = await fetch('http://localhost:5000/api/company/create-drive', {
        method: 'POST',
        headers: this.authHeaders(true),
        body: JSON.stringify(this.newDrive)
      });
      const data = await res.json();
      if (res.ok) {
        this.message = data.message;
        this.showForm = false;
        this.newDrive = {
          title: '',
          desc: '',
          cgpa: 0,
          branch: '',
          year: '',
          deadline: '',
          location: '',
          package_amount: ''
        };
        this.fetchDrives();
      } else {
        this.error = data.message || 'Failed to create drive';
      }
    },
    async updateStatus(id, status) {
      this.message = '';
      this.error = '';
      const res = await fetch(`http://localhost:5000/api/company/application/${id}/status`, {
        method: 'POST',
        headers: this.authHeaders(true),
        body: JSON.stringify({ status })
      });
      const data = await res.json();
      if (res.ok) {
        this.message = data.message;
        this.fetchDrives();
      } else {
        this.error = data.message || 'Failed to update status';
      }
    }
  },
  mounted() {
    this.fetchDrives();
  }
}
</script>
