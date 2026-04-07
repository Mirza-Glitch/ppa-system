<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center">
      <h2>Company Dashboard</h2>
      <button class="btn btn-primary" @click="showForm = !showForm">Create New Drive</button>
    </div>

    <div v-if="showForm" class="card p-3 my-3 bg-light">
      <h5>New Placement Drive</h5>
      <input v-model="newDrive.title" class="form-control mb-2" placeholder="Job Title">
      <input v-model="newDrive.cgpa" type="number" class="form-control mb-2" placeholder="Min CGPA">
      <textarea v-model="newDrive.desc" class="form-control mb-2" placeholder="Description"></textarea>
      <button @click="createDrive" class="btn btn-success">Submit for Approval</button>
    </div>

    <h4 class="mt-4">Active Drives & Applicants</h4>
    <div v-for="drive in myDrives" :key="drive.id" class="card mb-3">
      <div class="card-header d-flex justify-content-between">
        <strong>{{ drive.title }}</strong>
        <span class="badge bg-info">{{ drive.status }}</span>
      </div>
      <div class="card-body">
        <h6>Applicants:</h6>
        <ul>
          <li v-for="app in drive.applicants" :key="app.id">
            {{ app.student_name }} - 
            <button @click="updateStatus(app.id, 'Shortlisted')" class="btn btn-sm btn-link">Shortlist</button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      showForm: false,
      newDrive: { title: '', cgpa: '', desc: '' },
      myDrives: []
    };
  },
  methods: {
    async fetchDrives() {
      const res = await fetch('http://localhost:5000/api/company/drives', {
        headers: { 'Authorization': localStorage.getItem('token') }
      });
      this.myDrives = await res.json();
    },
    async createDrive() {
      await fetch('http://localhost:5000/api/company/create-drive', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': localStorage.getItem('token')
        },
        body: JSON.stringify(this.newDrive)
      });
      this.showForm = false;
      this.fetchDrives();
    }
  },
  mounted() { this.fetchDrives(); }
}
</script>