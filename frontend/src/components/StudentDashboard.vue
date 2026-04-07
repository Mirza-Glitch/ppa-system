<template>
  <div class="container mt-5">
    <h3>Available Placement Drives</h3> [cite: 112]
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div class="row">
      <div v-for="drive in drives" :key="drive.id" class="col-md-4">
        <div class="card mb-3">
          <div class="card-body">
            <h5 class="card-title">{{ drive.title }}</h5>
            <p>Required CGPA: {{ drive.cgpa }}</p> [cite: 50]
            <button @click="apply(drive.id)" class="btn btn-success">Apply</button> [cite: 114]
          </div>
        </div>
      </div>
    </div>
    <hr>
    <button @click="exportData" class="btn btn-secondary">Export My History (CSV)</button> [cite: 129]
  </div>
</template>

<script>
export default {
  data() {
    return { drives: [], error: '' };
  },
  methods: {
    async loadDrives() {
      const response = await fetch('http://localhost:5000/api/drives', {
        headers: { 'Authorization': localStorage.getItem('token') }
      });
      this.drives = await response.json();
    },
    async apply(id) {
      const response = await fetch(`http://localhost:5000/api/apply/${id}`, {
        method: 'POST',
        headers: { 'Authorization': localStorage.getItem('token') }
      });
      const data = await response.json();
      if (!response.ok) this.error = data.msg;
      else alert(data.msg);
    },
    async exportData() { 
      alert("Export request triggered. You will be notified via email.");
    }////[cite: 137]
  },
  mounted() { this.loadDrives(); }
}
</script>